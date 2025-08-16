import queue

import sounddevice as sd
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from vad.VoiceActivityDetector import VoiceActivityDetector, VAD_CHANNELS, VAD_SAMPLING_RATE, VAD_BLOCK_SIZE, \
    MAX_SILENCE_SAMPLES, VAD_POST_SPEECH_SECONDS


class RecorderWorker(QObject):
    finished = pyqtSignal()
    speech_detected = pyqtSignal()
    speech_lost = pyqtSignal()
    recording_done = pyqtSignal(list)
    status_update = pyqtSignal(str)  # Für Statusmeldungen
    error_occurred = pyqtSignal(str)  # Für Fehler
    silence = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.is_running = True
        self.is_recording_active = False  # Neue Variable für aktive Aufnahme
        self.vad = None
        self.audio_stream = None

    @pyqtSlot()
    def run_forever(self):
        """Dauerhaft laufender Worker"""
        self.status_update.emit("Recorder-Thread gestartet")

        try:
            # Initialisiere VAD einmal
            self.vad = VoiceActivityDetector()
            self.status_update.emit("VAD initialisiert")
        except Exception as e:
            self.error_occurred.emit(f"Fehler bei VAD-Initialisierung: {str(e)}")
            self.finished.emit()
            return

        while self.is_running:
            try:
                # Prüfe auf Aufgaben (mit Timeout)
                try:
                    task = self.task_queue.get(timeout=0.1)  # 100ms Timeout

                    if task.get("type") == "START_RECORDING":
                        self._start_continuous_recording()
                    elif task.get("type") == "STOP_RECORDING":
                        self._stop_continuous_recording()
                    elif task.get("type") == "STOP_WORKER":
                        break

                    self.task_queue.task_done()

                except queue.Empty:
                    # Keine Aufgaben, weiter mit VAD-Überwachung
                    pass

                # Führe kontinuierliche VAD-Überwachung durch
                if self.is_recording_active:
                    self._monitor_vad()

            except Exception as e:
                self.error_occurred.emit(f"Interner Fehler: {str(e)}")

        # Aufräumen
        self._cleanup()
        self.finished.emit()

    def _start_continuous_recording(self):
        """Starte kontinuierliche Aufnahme"""
        if not self.is_recording_active:
            try:
                # Stream öffnen, falls nicht bereits offen
                if self.audio_stream is None:
                    self.audio_stream = sd.InputStream(
                        callback=self.vad.audio_callback,
                        channels=VAD_CHANNELS,
                        samplerate=VAD_SAMPLING_RATE,
                        blocksize=VAD_BLOCK_SIZE
                    )
                    self.audio_stream.start()

                # VAD zurücksetzen
                self.vad.recording.clear()
                self.vad.silence_samples = 0
                self.vad.is_recording = False

                self.is_recording_active = True
                self.status_update.emit("Kontinuierliche Aufnahme gestartet")

            except Exception as e:
                self.error_occurred.emit(f"Fehler beim Starten der Aufnahme: {str(e)}")

    def _stop_continuous_recording(self):
        """Stoppe kontinuierliche Aufnahme"""
        if self.is_recording_active:
            self.is_recording_active = False

            # Sende letzte Aufnahme, falls vorhanden
            if self.vad and self.vad.recording:
                recording = self.vad.recording.copy()
                self.recording_done.emit(recording)
                self.vad.recording.clear()
            self.vad.is_recording = False
            self.status_update.emit("Kontinuierliche Aufnahme gestoppt")
            self.silence.emit(0)

    def _monitor_vad(self):
        """Überwache VAD kontinuierlich"""
        try:
            # Kurze Pause für Audio-Verarbeitung
            sd.sleep(100)

            if self.vad:
                # Prüfe auf Stille (Ende der Spracherkennung)
                if self.vad.silence_samples >= MAX_SILENCE_SAMPLES:
                    if self.vad.recording:
                        recording = self.vad.recording.copy()
                        self.recording_done.emit(recording)
                        self.vad.recording.clear()
                        self.status_update.emit(
                            f"⏹️ {VAD_POST_SPEECH_SECONDS} Sekunden Stille erkannt - Aufnahme beendet")

                    self.vad.silence_samples = 0

                # Sende Sprach-Erkennungs-Signale
                if self.vad.is_recording:
                    self.speech_detected.emit()
                    self.silence.emit(0)
                else:
                    self.speech_lost.emit()
                    if self.vad.recording:
                        self.silence.emit(self.vad.silence_samples)
                    else:
                        self.silence.emit(0)

        except Exception as e:
            self.error_occurred.emit(f"Fehler bei VAD-Überwachung: {str(e)}")

    def _cleanup(self):
        """Räume Ressourcen auf"""
        self.is_recording_active = False
        if self.audio_stream:
            try:
                self.audio_stream.stop()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None

    def start_recording(self):
        """Starte kontinuierliche Aufnahme (von außen aufgerufen)"""
        self.task_queue.put({"type": "START_RECORDING"})

    def stop_recording(self):
        """Stoppe kontinuierliche Aufnahme (von außen aufgerufen)"""
        self.task_queue.put({"type": "STOP_RECORDING"})

    def stop_worker(self):
        """Stoppe den gesamten Worker"""
        self.task_queue.put({"type": "STOP_WORKER"})

    def stop(self):
        """Kompatibilität mit altem Interface"""
        self.stop_worker()
