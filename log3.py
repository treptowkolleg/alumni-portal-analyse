import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
import sqlite3
import time
import requests
import os
from datetime import datetime
from threading import Thread
from queue import Queue

from resemblyzer import VoiceEncoder, preprocess_wav
from resemblyzer.hparams import sampling_rate
from sklearn.cluster import AgglomerativeClustering

# === Konfiguration ===
BLOCK_DURATION = 120  # Sekunden
SAMPLERATE = 16000
MODEL_SIZE = "medium"
OLLAMA_MODEL = "mistral"
LANGUAGE = "de"
NUM_CHANNELS = 1

# === Pfade & Setup ===
os.makedirs("audio", exist_ok=True)
DB_PATH = "protokolle.db"

# === Datenbank vorbereiten ===
conn_init = sqlite3.connect(DB_PATH)
cur_init = conn_init.cursor()
cur_init.execute('''
    CREATE TABLE IF NOT EXISTS protokoll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        block_nr INTEGER,
        transcript TEXT,
        summary TEXT
    )
''')
conn_init.commit()
conn_init.close()

# === Modelle vorbereiten ===
whisper = WhisperModel(MODEL_SIZE, compute_type="int8", device="cpu")
encoder = VoiceEncoder()

# === Warteschlange ===
audio_queue = Queue()
block_counter = 1

# === Aufnahmefunktion ===
def record_audio_block(duration, path):
    print(f"🎙️ [REC] {path} wird aufgenommen ({duration}s) …")
    audio = sd.rec(int(duration * SAMPLERATE), samplerate=SAMPLERATE, channels=NUM_CHANNELS)
    sd.wait()
    sf.write(path, audio, SAMPLERATE)
    print(f"💾 [SAVE] Gespeichert: {path}")

# === Sprechererkennung ===
def detect_speakers(audio_path):
    wav = preprocess_wav(audio_path)
    embeds, timestamps = encoder.embed_utterance(wav, return_partials=True)
    clustering = AgglomerativeClustering(n_clusters=4).fit(embeds)
    labels = clustering.labels_

    segments = []
    for time_segment, label in zip(timestamps, labels):
        start = round(time_segment[0], 1)
        end = round(time_segment[1], 1)
        segments.append((start, end, label))
    return segments

# === Verarbeitungsfunktion ===
def process_audio(path, block_nr):
    try:
        print(f"🧠 [WHISPER] Block {block_nr}: Starte Transkription …")
        # segments, _ = whisper.transcribe(path, language=LANGUAGE, word_timestamps=True)
        segments = list(whisper.transcribe(path, language=LANGUAGE, word_timestamps=True))
        whisper_segments = list(segments)
        if not whisper_segments:
            print(f"⚠️ [WHISPER] Kein Text erkannt.")
            return

        print(f"🎭 [SPEAKER] Block {block_nr}: Sprecheranalyse …")
        speaker_segments = detect_speakers(path)


        # Sprecher zuordnen nach Zeitfenster
        transcript = ""
        for seg in whisper_segments:
            start = round(seg.start, 1)
            end = round(seg.end, 1)
            text = seg.text.strip()
            speaker_id = "?"  # default
            for s_start, s_end, label in speaker_segments:
                if s_start <= start <= s_end:
                    speaker_id = label
                    break
            transcript += f"[Sprecher {speaker_id}] {text}\n"

        print(f"✅ [WHISPER+SPEAKER] Block {block_nr}: Transkript mit Sprecherlabels fertig.")

        # Zusammenfassung via Ollama
        print(f"🤖 [LLM] Block {block_nr}: Starte Zusammenfassung …")
        prompt = (
            "Hier ist ein wörtliches Transkript eines Gesprächsabschnitts auf Deutsch mit Sprecherkennzeichnung:\n\n"
            f"{transcript}\n\n"
            "Bitte fasse den Inhalt in 2–3 kurzen Sätzen stichpunktartig zusammen. "
            "Ignoriere Wiederholungen. Antworte nur mit der Zusammenfassung:"
        )

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            summary = response.json()["response"].strip()
            print(f"✅ [LLM] Zusammenfassung abgeschlossen.")
        except Exception as e:
            summary = f"[FEHLER bei Zusammenfassung: {e}]"
            print(summary)

        # Datenbank speichern
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        cur.execute(
            "INSERT INTO protokoll (timestamp, block_nr, transcript, summary) VALUES (?, ?, ?, ?)",
            (ts, block_nr, transcript, summary)
        )
        conn.commit()
        conn.close()
        print(f"📥 [DB] Block {block_nr} gespeichert.")

    except Exception as e:
        print(f"❌ [FEHLER] Block {block_nr}: {e}")

# === Threads ===
def recorder():
    global block_counter
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio/block_{block_counter}_{timestamp}.wav"
        record_audio_block(BLOCK_DURATION, filename)
        audio_queue.put((filename, block_counter))
        block_counter += 1

def processor():
    while True:
        path, block_nr = audio_queue.get()
        process_audio(path, block_nr)
        audio_queue.task_done()

# === Hauptprogramm ===
if __name__ == "__main__":
    print("🔴 Aufnahme läuft. Drücke [Strg+C], um zu stoppen …")
    Thread(target=recorder, daemon=True).start()
    processor_thread = Thread(target=processor)
    processor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Aufnahme gestoppt. Warte auf letzte Verarbeitung …")
        audio_queue.join()
        print("✅ Beendet. Alle Daten gespeichert.")
