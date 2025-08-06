import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal

from vad.VoiceActivityDetector import VoiceActivityDetector, VAD_CHANNELS, VAD_SAMPLING_RATE, VAD_BLOCK_SIZE, \
    MAX_SILENCE_SAMPLES, VAD_POST_SPEECH_SECONDS


class RecorderWorker(QObject):
    finished = pyqtSignal()
    started = pyqtSignal()
    speech_detected = pyqtSignal()
    speech_lost = pyqtSignal()
    recording_done = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.is_stopped = False
        self.is_running = True
        self.recording = []

    def run(self):
        self.started.emit()
        vad = VoiceActivityDetector()

        with sd.InputStream(callback=vad.audio_callback, channels=VAD_CHANNELS, samplerate=VAD_SAMPLING_RATE,
                            blocksize=VAD_BLOCK_SIZE):
            while self.is_running:
                sd.sleep(100)
                if vad.silence_samples >= MAX_SILENCE_SAMPLES:
                    self.recording = vad.recording
                    print(f"⏹️ \t{VAD_POST_SPEECH_SECONDS} Sekunden Stille erkannt")
                    vad.silence_samples = 0

                    if self.recording:
                        self.recording_done.emit(self.recording)
                        self.recording = []
                        vad.recording.clear()

                if self.is_stopped:
                    self.recording = vad.recording
                    print(f"⏹️ \tAufnahme gestoppt")
                    break

                if vad.is_recording:
                    self.speech_detected.emit()
                else:
                    self.speech_lost.emit()

        if self.recording:
            self.recording_done.emit(self.recording)
        self.finished.emit()