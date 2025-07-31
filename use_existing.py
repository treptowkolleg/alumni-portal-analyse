import os
import re
import sqlite3
import threading
import time
import wave
from datetime import datetime
from queue import Queue
from threading import Thread

from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from sklearn.decomposition import PCA

import librosa
import matplotlib.pyplot as plt
import numpy as np
import requests
import sounddevice as sd
import soundfile as sf
import torch
from faster_whisper import WhisperModel
from resemblyzer import VoiceEncoder, preprocess_wav, wav_to_mel_spectrogram
from resemblyzer.hparams import sampling_rate
from scipy.ndimage import uniform_filter1d
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import SpectralClustering
from sklearn.manifold import SpectralEmbedding
from sklearn.preprocessing import normalize
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

print(f"Backend für CUDA aktiviert: {torch.backends.cudnn.enabled}")
print(f"CUDA-Version: {torch.version.cuda}")
print(f"CUDA verfügbar: {torch.cuda.is_available()}")

# === Konfiguration ===
BLOCK_DURATION = 90  # Sekunden
SAMPLERATE = 16000
MODEL_SIZE = "medium"
threshold = 0.5
best_threshold = 0

# neu implementieren:
USE_EXISTING_AUDIO_FILES = True  # Auf True setzen, um vorhandene Dateien zu verarbeiten
EXISTING_AUDIO_DIR = "audio"  # Verzeichnis mit den vorhandenen Audio-Dateien

models = {
    0: "eas/neuralbeagle14",    # sehr schlechte Zusammenfassung, es wird hauptsächlich direkt wiedergegeben.
    1: "gemma3n:e4b",           # fängt an, bei längeren Prompts Mumpitz zu machen. Ansonsten sehr gut. Bisher bestes Deutsch.
    2: "openhermes",            # inhaltliche Zusammenfassung ist gut. Deutschkenntnisse ausreichend.
    3: "llama3.1",              # zu ungenau bzw. zu allgemein. geht kaum auf den Inhalt ein, auch wenn dieser eher kurz ist.
    4: "deepseek-r1:8b",        # entspricht nicht dem Gesagten. Es wurde der Prompt mit ins Protokoll eingearbeitet. Think macht den Prozess langsam.
    5: "qwen3:8b",              # gute Zusammenfassung, jedoch wurde der Gesprächsverlauf bewertet, was unnötig ist. Think macht den Prozess langsam.
}

# Model-Auswahl
OLLAMA_MODEL = models[0]

LANGUAGE = "de"
NUM_CHANNELS = 1
GPU = torch.cuda.get_device_name(0) if torch.backends.cudnn.enabled and torch.cuda.is_available() else "None"
device = "cuda" if torch.cuda.is_available() else "cpu"
rec_length = 0
duration = 0

# === Pfade & Setup ===
os.makedirs("audio", exist_ok=True)
DB_PATH = "protokolle.db"
stop_event = threading.Event()

# === Datenbank vorbereiten ===
conn_init = sqlite3.connect(DB_PATH)
cur_init = conn_init.cursor()
cur_init.execute('''
    CREATE TABLE IF NOT EXISTS protokoll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        block_nr INTEGER,
        transcript TEXT,
        summary TEXT,
        whisper_model TEXT,
        whisper_duration REAL,
        llm_model TEXT,
        llm_duration REAL,
        device TEXT,
        gpu TEXT,
        audio_length TEXT
    )
''')
conn_init.commit()
conn_init.close()

# === Modelle vorbereiten ===
whisper = WhisperModel(MODEL_SIZE, compute_type="int8", device=device)
encoder = VoiceEncoder()

# === Warteschlange ===
audio_queue = Queue()
block_counter = 1


def process_existing_audio_files():
    """Verarbeitet alle vorhandenen WAV-Dateien im angegebenen Verzeichnis"""
    global block_counter

    if not os.path.exists(EXISTING_AUDIO_DIR):
        print(f"⚠️ Verzeichnis {EXISTING_AUDIO_DIR} existiert nicht")
        return

    # Finde alle WAV-Dateien und sortiere sie nach Erstellungsdatum
    audio_files = [f for f in os.listdir(EXISTING_AUDIO_DIR) if f.endswith('.wav')]
    audio_files.sort(key=lambda x: os.path.getctime(os.path.join(EXISTING_AUDIO_DIR, x)))

    if not audio_files:
        print("⚠️ Keine WAV-Dateien im Audio-Verzeichnis gefunden")
        return

    print(f"🔍 {len(audio_files)} vorhandene Audio-Dateien gefunden. Starte Verarbeitung...")

    # Setze block_counter auf die höchste vorhandene Blocknummer + 1
    existing_blocks = [int(f.split('_')[1]) for f in audio_files if f.startswith('block_')]
    if existing_blocks:
        block_counter = max(existing_blocks) + 1

    for filename in audio_files:
        file_path = os.path.join(EXISTING_AUDIO_DIR, filename)
        audio_queue.put((file_path, block_counter))
        block_counter += 1


# === Aufnahmefunktion ===
def record_audio_block(duration, path):
    global rec_length

    print(f"🎙️ [REC] {path} wird aufgenommen ({duration}s) …")

    rec_length = time.perf_counter()
    audio = sd.rec(int(duration * SAMPLERATE), samplerate=SAMPLERATE, channels=NUM_CHANNELS)
    sd.wait()
    sf.write(path, audio, SAMPLERATE)
    print(f"💾 [SAVE] Gespeichert: {path}")

    rec_length = time.perf_counter() - rec_length


# === Sprechererkennung ===
def detect_speakers(audio_path, min_segment_length=3.0):
    global duration
    global best_threshold
    global threshold
    duration = 0
    try:
        # 1. Audio vorverarbeiten
        wav = preprocess_wav(audio_path)
        duration = len(wav) / sampling_rate
        print(f"🔊 Audiolänge: {duration:.2f}s")

        # 1.2 Spektrum anzeigen
        spec = wav_to_mel_spectrogram(wav)


        # Hüllkurve berechnen: geglättete Amplitude
        rms = librosa.feature.rms(y=wav, frame_length=1024, hop_length=512)[0]
        frames = np.arange(len(rms))
        times_rms = librosa.frames_to_time(frames, sr=sampling_rate, hop_length=512)

        # Mel-Spektrogramm berechnen
        spec = wav_to_mel_spectrogram(wav)
        spec_db = 20 * np.log10(np.maximum(spec, 1e-5))

        # Mel-Frequenzen berechnen für Y-Achse
        n_mels = spec.shape[0]
        mel_freqs = librosa.mel_frequencies(n_mels=n_mels, fmin=0, fmax=sampling_rate / 2)

        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

        # Waveform
        ax1.plot(times_rms, rms, color='cyan')
        ax1.set_title("RMS-Hüllkurve (librosa)", color='white')
        ax1.set_xlabel("Zeit (s)", color='white')
        ax1.set_ylabel("RMS-Lautstärke", color='white')
        ax1.grid(True, color='gray', alpha=0.3)
        ax1.tick_params(colors='white')

        # Mel-Spektrogramm mit kHz-Beschriftung
        extent = [0, duration, mel_freqs[0], mel_freqs[-1]]
        im = ax2.imshow(spec_db.T, aspect="auto", origin="lower", cmap="viridis", extent=extent)
        ax2.set_title("Mel-Spektrogramm (dB, Frequenz in kHz)", color='white')
        ax2.set_xlabel("Zeit (s)", color='white')
        ax2.set_ylabel("Frequenz (Hz)", color='white')
        ax2.grid(True, color='gray', alpha=0.3)
        ax2.tick_params(colors='white')

        fig.suptitle(f"Analyse für Audio '{audio_path.split('/')[-1]}'", fontsize=14, color='white')
        fig.patch.set_facecolor('#121212')
        ax1.set_facecolor("#222222")
        ax2.set_facecolor("#222222")

        # y-Achse in kHz beschriften
        ticks = [0, 1000, 2000, 4000, 6000, 8000]
        ax2.set_yticks(ticks)
        ax2.set_yticklabels([f"{t // 1000}k" for t in ticks])


        plt.tight_layout()
        plt.show()


        # 2. Manuelle Segmentierung für kurze Audios
        if duration < 10.0:  # Wenn Audio sehr kurz
            print("⚠️ Audio zu kurz - verwende Single-Speaker-Modus")
            return [(0.0, duration, 0)]

        # 3. Embedding mit Sliding Window extrahieren
        window_size = 2  # Sekunden
        hop_size = 0.75  # Sekunden
        segments = []

        for start in np.arange(0, duration - window_size, hop_size):
            end = start + window_size
            segment = wav[int(start * sampling_rate):int(end * sampling_rate)]

            # Embedding für jedes Segment
            embed = encoder.embed_utterance(segment)
            segments.append((start, end, embed))

        if not segments:
            return [(0.0, duration, 0)]

        # 4. Clustering durchführen
        embeddings = np.array([e for (_, _, e) in segments])

        # Vektoren normalisieren (für cosine-Distanz erforderlich)
        embeddings_normalized = normalize(embeddings, norm='l2')
        similarity_matrix = cosine_similarity(embeddings_normalized)
        sigma = 0.5  # anpassen!
        affinity_matrix = np.exp(-1 * (1 - similarity_matrix) ** 2 / (2 * sigma ** 2))

        reduced = PCA(n_components=2).fit_transform(embeddings_normalized)

        scores = []
        for k in range(2, 10):
            clustering = SpectralClustering(n_clusters=k, affinity='precomputed').fit(affinity_matrix)
            score = silhouette_score(embeddings_normalized, clustering.labels_)
            scores.append(score)

        beste_anzahl = 2 + np.argmax(scores)

        print(f"Beste Anzahl der Sprecher: {beste_anzahl}")

        clustering = SpectralClustering(
            n_clusters=beste_anzahl,
            affinity='precomputed',
            assign_labels='kmeans',
            random_state=42
            ).fit(affinity_matrix)
        # 2D-Embedding für Visualisierung
        embedding = SpectralEmbedding(n_components=beste_anzahl, affinity='precomputed')
        X_embedded = embedding.fit_transform(affinity_matrix)

        labels = clustering.labels_
        num_clusters = len(set(labels))

        print(f"gefundene Cluster: {num_clusters}")



        plt.figure(figsize=(8, 6))
        plt.scatter(X_embedded[:, 0], X_embedded[:, 1], c=labels, cmap='tab10', s=50)
        plt.title(f'Clustering mit {num_clusters} Clustern (Spectral Embedding)')
        plt.colorbar(label='Cluster Label')
        plt.show()

        # 5. Sprechersegmente erstellen
        speaker_segments = []
        for (start, end, _), label in zip(segments, labels):
            speaker_segments.append((start, end, label))

        if True:
            plt.figure(figsize=(10, 2))
            for (start, end, label) in speaker_segments:
                if label == -1:
                    color = 'gray'
                else:
                    color = f"C{label % 10}"
                plt.plot([start, end], [label, label], lw=6, color=color)
            plt.title("Sprechersegmente (Spectral Clustering)")
            plt.xlabel("Zeit (s)")
            plt.ylabel("Sprecher-ID")
            plt.grid(True)
            plt.tight_layout()
            plt.show()

        # 6. Benachbarte Segmente gleicher Sprecher zusammenführen
        merged = []
        for seg in speaker_segments:
            if merged and seg[2] == merged[-1][2] and seg[0] - merged[-1][1] < 2.0:
                merged[-1] = (merged[-1][0], seg[1], seg[2])
            else:
                merged.append(seg)

        # 7. Kurze Segmente filtern
        final_segments = [s for s in merged if s[1] - s[0] >= min_segment_length]

        if not final_segments:
            return [(0.0, duration, 0)]

        return final_segments

    except Exception as e:
        print(f"Fehler in detect_speakers: {str(e)}")
        return [(0.0, duration if 'duration' in locals() else 30.0, 0)]


# === Verarbeitungsfunktion ===
def process_audio(path, block_nr):
    global device
    global threshold
    global GPU
    global MODEL_SIZE
    global OLLAMA_MODEL
    llm_stop_time = 0.0
    think = ""

    length_seconds = get_wav_length(path)

    try:
        print(f"🧠 [WHISPER] Block {block_nr}: Starte Transkription …")

        whisper_start_time = time.perf_counter()
        segments, _ = whisper.transcribe(path, language=LANGUAGE, word_timestamps=True)

        whisper_segments = list(segments)
        if not whisper_segments:
            print(f"⚠️ [WHISPER] Kein Text erkannt.")
            return

        print(f"🎭 [SPEAKER] Block {block_nr}: Sprecheranalyse …")
        speaker_segments = detect_speakers(path)

        # Sprecher zuordnen nach Zeitfenster
        transcript = ""

        for seg_idx, seg in enumerate(whisper_segments):
            start = round(seg.start, 1)
            end = round(seg.end, 1)
            text = seg.text.strip()
            speaker_id = "?"
            matched_embedding = None

            # Suche nach passendem Sprecher-Segment
            for s_start, s_end, label in speaker_segments:  # Jetzt mit Embedding
                if s_start <= start <= s_end:
                    speaker_id = label
                    break

            transcript += f"[Sprecher {speaker_id}] {text}\n"

        print(f"✅ [WHISPER+SPEAKER] Block {block_nr}: Transkript mit Sprecherlabels fertig.")

        whisper_stop_time = time.perf_counter() - whisper_start_time

        # Zusammenfassung via Ollama
        # TODO: Schleife bauen, damit alle eingetragenen LLMs die gleiche Datei verwursten.
        print(f"🤖 [LLM] Block {block_nr}: Starte Zusammenfassung …")

        llm_start_time = time.perf_counter()

        prompt = (
            "Erstelle aus dem folgenden Transkript ein sachliches, strukturiertes Protokoll. Achte auf klare Gliederung, chronologische Reihenfolge und korrekte inhaltliche Wiedergabe."
            ""
            "Verwende dabei folgende Struktur:"
            "- Thema"
            "- Datum (falls vorhanden im Text)"
            "- Teilnehmende (falls erkennbar)"
            "- Besprochene Punkte"
            "-> Halte Entscheidungen, Meinungen, Argumente und Ergebnisse sachlich fest."
            "- Ergebnisse und Vereinbarungen"
            ""
            "Verwende keine direkte Rede. Der Stil soll sachlich und neutral sein."
            ""
            "Transkript:"
            f"{transcript}\n\n"
        )

        # prompt = (
        #     "Hier ist ein wörtliches Transkript auf Deutsch mit Sprecherkennzeichnung:\n\n"
        #     "Bitte fasse den Inhalt strukturiert und umfangreich zusammen. Beziehe wichtige Infos mit ein. Wenn vorhanden, notiere Handlungsanweisungen und To-Do's."
        #     ""
        #     "Transkript:"
        #     ""
        #     f"{transcript}\n\n"
        # )

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            summary = response.json()["response"].strip()

            match = re.search(r"<think>(.*?)</think>", summary, re.DOTALL)
            think = match.group(1).strip() if match else ""

            # Entferne das gesamte <think>...</think>-Tag aus dem summary
            summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.DOTALL).strip()

            print(f"✅ [LLM] Zusammenfassung abgeschlossen.")

            llm_stop_time = time.perf_counter() - llm_start_time

        except Exception as e:
            summary = f"[FEHLER bei Zusammenfassung: {e}]"
            print(summary)

        # Datenbank speichern
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        ts = datetime.now().isoformat()
        cur.execute(
            "INSERT INTO protokoll (timestamp, block_nr, transcript, think, summary, whisper_model, whisper_duration, llm_model, llm_duration, device, gpu, audio_length, threshold) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ts, block_nr, transcript, think, summary, MODEL_SIZE, whisper_stop_time, OLLAMA_MODEL, llm_stop_time, device, GPU,
             f"{duration:.2f}s", threshold)
        )
        conn.commit()
        conn.close()
        print(f"📥 [DB] Block {block_nr} gespeichert.")

    except Exception as e:
        print(f"❌ [FEHLER] Block {block_nr}: {e}")


def get_wav_length(filename):
    with wave.open(filename, 'rb') as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        duration = frames / float(rate)
    return duration


# === Threads ===
def recorder():
    global block_counter
    while not stop_event.is_set():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio/block_{block_counter}_{timestamp}.wav"
        record_audio_block(BLOCK_DURATION, filename)
        audio_queue.put((filename, block_counter))
        block_counter += 1


def processor():
    while not (stop_event.is_set() and audio_queue.empty()):
        path, block_nr = audio_queue.get()
        process_audio(path, block_nr)
        audio_queue.task_done()


# === Hauptprogramm ===
if __name__ == "__main__":
    recorder_thread = None
    if USE_EXISTING_AUDIO_FILES:
        process_existing_audio_files()
    else:
        print("🔴 Aufnahme läuft. Drücke [Strg+C], um zu stoppen …")
        recorder_thread = Thread(target=recorder, daemon=True)
        recorder_thread.start()

    processor_thread = Thread(target=processor)
    processor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Aufnahme gestoppt. Warte auf letzte Verarbeitung …")
        stop_event.set()  # 🧨 Beende beide Threads
        if not USE_EXISTING_AUDIO_FILES:
            recorder_thread.join()  # 🎤 Warten auf Beenden des Recorders
        audio_queue.join()  # ⏳ Warten bis alles verarbeitet ist
        processor_thread.join()  # 🧠 Warten auf Beenden des Verarbeiters
        print("✅ Beendet. Alle Daten gespeichert.")