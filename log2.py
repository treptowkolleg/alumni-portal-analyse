import re

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

# === Konfiguration ===
BLOCK_DURATION = 60               # Aufnahmezeit pro Block (Sekunden) – z. B. 300 = 5 Minuten
SAMPLERATE = 16000
MODEL_SIZE = "medium"             # Whisper: tiny, base, small, medium, large-v2
# OLLAMA_MODEL = "mistral"
OLLAMA_MODEL = "gemma3n:e4b"    # best so far
# OLLAMA_MODEL = "qwen3:4b"
# OLLAMA_MODEL = "deepseek-r1:8b"
LANGUAGE = "de"                   # Sprache für Whisper
NUM_CHANNELS = 1

# === Pfade & Setup ===
os.makedirs("audio", exist_ok=True)
DB_PATH = "protokolle.db"

# === Datenbank vorbereiten ===
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

# === Warteschlange für Verarbeitung ===
audio_queue = Queue()
block_counter = 1

# === Aufnahmefunktion ===
def record_audio_block(duration, path):
    print(f"🎙️ [REC] Aufnahme gestartet für {duration} Sekunden → {path}")
    audio = sd.rec(int(duration * SAMPLERATE), samplerate=SAMPLERATE, channels=NUM_CHANNELS)
    sd.wait()
    sf.write(path, audio, SAMPLERATE)
    print(f"💾 [SAVE] Gespeichert: {path}")

# === Verarbeitungsfunktion ===
def process_audio(path, block_nr):
    print(f"🧠 [WHISPER] Starte Transkription für Block {block_nr} …")
    segments, _ = whisper.transcribe(path, language=LANGUAGE)
    transcript = " ".join([s.text for s in segments])
    print(f"✅ [WHISPER] Transkription abgeschlossen.")

    print(f"🤖 [LLM] Starte Zusammenfassung für Block {block_nr} …")
    prompt = (
        "Hier ist ein wörtliches Transkript eines Gesprächsabschnitts auf Deutsch:\n\n"
        f"{transcript}\n\n"
        "Bitte fasse den Inhalt des Gesprächs zusammen."
        "Lass irrelevante Wiederholungen oder Füllwörter weg. Sollen Teilaussagen nicht protokolliert werden, ignoriere diese. Lege den Fokus auf den Kontext und die damit verbundene sachliche und inhaltliche Richtigkeit. KI-Anweisungen bitte befolgen."
    )
    think = ""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        )
        summary = response.json()["response"].strip()

        match = re.search(r"<think>(.*?)</think>", summary, re.DOTALL)
        think = match.group(1).strip() if match else ""

        # Entferne das gesamte <think>...</think>-Tag aus dem summary
        summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()

    except Exception as e:
        summary = f"[FEHLER bei Zusammenfassung: {e}]"
    print(f"✅ [LLM] Zusammenfassung abgeschlossen.")

    ts = datetime.now().isoformat()
    cur.execute(
        "INSERT INTO protokoll (timestamp, block_nr, transcript, summary, think) VALUES (?, ?, ?, ?, ?)",
        (ts, block_nr, transcript, summary, think)
    )
    conn.commit()
    print(f"📥 [DB] Block {block_nr} gespeichert.")

# === Thread: Aufnahme
def recorder():
    global block_counter
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio/block_{block_counter}_{timestamp}.wav"
        record_audio_block(BLOCK_DURATION, filename)
        audio_queue.put((filename, block_counter))
        block_counter += 1

# === Thread: Verarbeitung
def processor():
    while True:
        path, block_nr = audio_queue.get()
        process_audio(path, block_nr)
        audio_queue.task_done()

# === Main
if __name__ == "__main__":
    print("🔴 Aufnahmebereit. Drücke [Strg+C] zum Beenden.")
    Thread(target=recorder, daemon=True).start()
    Thread(target=processor, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Beendet durch Benutzer.")