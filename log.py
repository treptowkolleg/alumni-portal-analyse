import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
import sqlite3
import time
import requests
from datetime import datetime
import os

# === Konfiguration ===
BLOCK_DURATION = 180        # 1 Minute für den ersten Test
SAMPLERATE = 16000
MODEL_SIZE = "medium"        # Whisper-Modell: base = schnell, medium = besser
OLLAMA_MODEL = "mistral"   # Erst mistral, später mixtral
LANGUAGE = "de"

# === Ordner & DB vorbereiten ===
os.makedirs("audio", exist_ok=True)
conn = sqlite3.connect("protokolle.db")
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS protokoll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    block_nr INTEGER,
    transcript TEXT,
    summary TEXT
)
''')
conn.commit()

# === Whisper vorbereiten ===
whisper = WhisperModel(MODEL_SIZE, compute_type="int8")

# === Aufnahme ===
def record_block(duration, filename):
    print(f"🎙️ Aufnahme {duration} Sekunden läuft...")
    audio = sd.rec(int(duration * SAMPLERATE), samplerate=SAMPLERATE, channels=1)
    sd.wait()
    sf.write(filename, audio, SAMPLERATE)
    print(f"💾 Gespeichert: {filename}")

# === Transkription
def transcribe_audio(path):
    segments, _ = whisper.transcribe(path, language=LANGUAGE)
    return " ".join([s.text for s in segments])

# === Zusammenfassung via Ollama
def summarize(text):
    prompt = (
        "Hier ist ein wörtliches Transkript eines Gesprächsabschnitts auf Deutsch:\n\n"
        f"{text}\n\n"
        "Bitte fasse den Inhalt des Gesprächs in 2–3 kurzen Sätzen stichpunktartig zusammen. "
        "Lass irrelevante Wiederholungen oder Füllwörter weg. Antworte nur mit der Zusammenfassung:"
    )
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    )
    return response.json()["response"].strip()

# === Speichern in DB
def save_to_db(block_nr, transcript, summary):
    ts = datetime.now().isoformat()
    cur.execute("INSERT INTO protokoll (timestamp, block_nr, transcript, summary) VALUES (?, ?, ?, ?)",
                (ts, block_nr, transcript, summary))
    conn.commit()
    print(f"✅ Block {block_nr} gespeichert.\n")

# === Hauptloop
def start_session():
    print("🔴 Aufnahmebereit. Drücke [Enter], um zu starten.")
    input()

    block = 1
    try:
        while True:
            print(f"\n🔄 Block {block}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"audio/block_{block}_{timestamp}.wav"

            record_block(BLOCK_DURATION, path)
            text = transcribe_audio(path)
            summary = summarize(text)
            save_to_db(block, text, summary)
            block += 1

    except KeyboardInterrupt:
        print("🛑 Aufnahme beendet durch Benutzer.")

# === Start
if __name__ == "__main__":
    start_session()