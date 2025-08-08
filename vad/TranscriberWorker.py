import queue
import time

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

from vad.AudioTranscriber import AudioTranscriber


class TranscriberWorker(QObject):
    transcription_ready = pyqtSignal(list)  # Für Transkriptionsergebnisse
    status_update = pyqtSignal(str)  # Für Statusmeldungen
    error_occurred = pyqtSignal(str)  # Für Fehlermeldungen
    task_completed = pyqtSignal()  # Für einzelne Aufgaben-Fertigstellung
    progress_update = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.is_running = True
        self.transcriber = None
        self._initialize_transcriber()

    def _initialize_transcriber(self):
        """Initialisiere den AudioTranscriber"""
        try:
            self.transcriber = AudioTranscriber()
            self.status_update.emit("Transkriptionsmodell geladen")
        except Exception as e:
            self.error_occurred.emit(f"Fehler beim Laden des Transkriptionsmodells: {str(e)}")

    @pyqtSlot()
    def run_forever(self):
        """Dauerhaft laufender Worker"""
        self.status_update.emit("Transkriptions-Thread gestartet")

        while self.is_running:
            try:
                # Warte auf Aufgaben (mit Timeout)
                try:
                    task = self.task_queue.get(timeout=0.1)  # 100ms Timeout

                    if task.get("type") == "TRANSCRIBE":
                        self._process_transcription(task)
                    elif task.get("type") == "STOP_WORKER":
                        break

                    self.task_queue.task_done()

                except queue.Empty:
                    # Keine Aufgaben vorhanden, weiterlaufen
                    pass

            except Exception as e:
                self.error_occurred.emit(f"Interner Fehler im Transkriptions-Worker: {str(e)}")

        # self.finished.emit()

    def _process_transcription(self, task):
        """Verarbeite eine einzelne Transkriptionsaufgabe"""
        if not self.transcriber:
            self.error_occurred.emit("Transkriptionsmodell nicht verfügbar")
            return

        recording = task.get("recording")
        task_id = task.get("task_id", "unknown")

        if not recording:
            self.error_occurred.emit("Keine Aufnahme zum Transkribieren vorhanden")
            return

        try:
            self.status_update.emit(f"Starte Transkription (Task: {task_id})")
            self._start_progress_simulation()

            # Transkription durchführen
            result = self.transcriber.process_recording(recording)

            # Ergebnis senden
            self.transcription_ready.emit(result)
            self.status_update.emit(f"Transkription abgeschlossen (Task: {task_id})")
            self._stop_progress_simulation()
            self.task_completed.emit()

        except Exception as e:
            error_msg = f"Transkriptionsfehler (Task: {task_id}): {str(e)}"
            self.error_occurred.emit(error_msg)
            self._stop_progress_simulation()

    def add_transcription_task(self, recording, task_id=None):
        """Füge eine Transkriptionsaufgabe zur Warteschlange hinzu"""
        if not task_id:
            task_id = str(time.time())  # Eindeutige ID generieren

        task = {
            "type": "TRANSCRIBE",
            "recording": recording,
            "task_id": task_id
        }
        self.task_queue.put(task)
        self.status_update.emit(f"Transkriptionsaufgabe hinzugefügt (Task: {task_id})")

    def stop_worker(self):
        """Stoppe den Worker ordentlich"""
        self.is_running = False
        self.task_queue.put({"type": "STOP_WORKER"})

    # Kompatibilität mit altem Interface
    def stop(self):
        self.stop_worker()

    def _start_progress_simulation(self):
        """Starte simulierte Fortschrittsanzeige"""
        self.simulation_running = True
        self.simulation_value = 0
        self._simulate_progress()

    def _simulate_progress(self):
        """Simuliere Fortschritt"""
        if self.simulation_running:
            self.progress_update.emit(100, 100)
            # Nächster Schritt in 200ms
            QTimer.singleShot(50, self._simulate_progress)

    def _stop_progress_simulation(self):
        """Stoppe simulierte Fortschrittsanzeige"""
        self.simulation_running = False
        self.progress_update.emit(0, 100)
