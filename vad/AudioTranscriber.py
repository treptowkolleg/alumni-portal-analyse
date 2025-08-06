import numpy as np
import soundfile as sf
from PyQt6.QtCore import QObject, pyqtSignal
from faster_whisper import WhisperModel
from scipy.io.wavfile import write

from tools.desktop import CPU_DEVICE, WHISPER_MODEL_SIZE
from vad.VoiceActivityDetector import VAD_SAMPLING_RATE, read_audio

whisper = WhisperModel(WHISPER_MODEL_SIZE, compute_type="int8", device=CPU_DEVICE)


class AudioTranscriber(QObject):
    transcription_ready = pyqtSignal(list)

    id_count = 0

    def __init__(self, parent=None):
        super().__init__(parent)

    def process_recording(self, recording):
        audio_data = np.concatenate(recording)
        write("output.wav", VAD_SAMPLING_RATE, (audio_data * 32767).astype(np.int16))
        print("💬 \tAufnahme wird transkribiert")

        # --------------------------
        # Segment-Analyse mit get_speech_timestamps
        # --------------------------
        wav = read_audio("output.wav", sampling_rate=VAD_SAMPLING_RATE)
        audio_data, sr = sf.read("output.wav")

        segments, _ = whisper.transcribe(audio_data, language="de", word_timestamps=False)

        whisper_segments = list(segments)
        if not whisper_segments:
            self.transcription_ready.emit([])
            print(f"⚠️ \tKeinen Text erkannt")
        else:
            result = []
            for seg_idx, seg in enumerate(whisper_segments):
                result.append({
                    "id": self.id_count,
                    "start": round(seg.start, 1),
                    "end": round(seg.end, 1),
                    "text": seg.text.strip()
                })
                print(f"{seg_idx}:\t{seg.text.strip()}")
                self.id_count += 1

            self.transcription_ready.emit(result)

        print("⏹️ \tDurchgang beendet")
