from collections import deque

import sounddevice as sd
import soundfile as sf
import numpy as np

from scipy.io.wavfile import write
from faster_whisper import WhisperModel

import torch

MODEL_SIZE = "medium"
LANGUAGE = "de"
GPU = torch.cuda.get_device_name(0) if torch.backends.cudnn.enabled and torch.cuda.is_available() else "None"
device = "cuda" if torch.cuda.is_available() else "cpu"

whisper = WhisperModel(MODEL_SIZE, compute_type="float32", device=device)


# torch.hub.download_url_to_file('https://models.silero.ai/vad_models/de.wav', 'de_example.wav')

# --------------------------
# Silero VAD vorbereiten
# --------------------------
model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                               model='silero_vad',
                               force_reload=False)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

sampling_rate = 16000
block_size = 512
channels = 1

# VAD-Thresholds
pre_speech_padding = int(0.5 * sampling_rate)
post_speech_padding = int(0.5 * sampling_rate)

pre_buffer = deque(maxlen=pre_speech_padding)
recording = []
is_recording = False
post_speech_countdown = 0

silence_samples = 0
max_silence_samples = 5 * sampling_rate


def simple_vad(audio_np):
    audio_tensor = torch.from_numpy(audio_np).float().unsqueeze(0)
    return model(audio_tensor, sampling_rate).item()

def audio_callback(indata, frames, time, status):
    global is_recording, recording, post_speech_countdown, silence_samples

    audio = indata[:, 0]
    pre_buffer.extend(audio)  # pre_buffer ist deque von einzelnen Samples

    speech_prob = simple_vad(audio)

    if speech_prob > 0.6:
        if not is_recording:
            print("🔴 \tSprache erkannt")
            silence_samples = 0
            recording.append(np.array(pre_buffer))
        is_recording = True
        post_speech_countdown = post_speech_padding
        recording.append(audio.copy())
    else:
        if is_recording:
            if post_speech_countdown > 0:
                recording.append(audio.copy())
                post_speech_countdown -= len(audio)
            else:
                print("⏸️ \tAufnahme pausiert")
                is_recording = False
        silence_samples += len(audio)

# --------------------------
# Aufnahme starten
# --------------------------

try:
    print("▶️ \tAufnahme bereit")
    with sd.InputStream(callback=audio_callback,
                        channels=channels,
                        samplerate=sampling_rate,
                        blocksize=block_size):
        while True:
            sd.sleep(100)
            # Hier prüfen, ob Stille zu lang ist
            if silence_samples >= max_silence_samples:
                print("⏹️ \t5 Sekunden Stille erkannt")
                break
except KeyboardInterrupt:
    pass

# --------------------------
# Datei speichern
# --------------------------
if recording:
    audio_data = np.concatenate(recording)
    write("output.wav", sampling_rate, (audio_data * 32767).astype(np.int16))
    print("💬 \tAufnahme wird transkribiert")

    # --------------------------
    # Segment-Analyse mit get_speech_timestamps
    # --------------------------
    wav = read_audio("output.wav", sampling_rate=sampling_rate)
    audio_data, sr = sf.read("output.wav")

    segments, _ = whisper.transcribe(audio_data, language=LANGUAGE, word_timestamps=False)

    whisper_segments = list(segments)
    if not whisper_segments:
        print(f"⚠️ \tKeinen Text erkannt")
    else:
        for seg_idx, seg in enumerate(whisper_segments):
            start = round(seg.start, 1)
            end = round(seg.end, 1)
            print(f"{seg_idx:2}:\t{seg.text.strip()}")
    print("⏹️ \tDurchgang beendet")

else:
    print("⏹️ \tKeine Sprache erkannt – nichts gespeichert")