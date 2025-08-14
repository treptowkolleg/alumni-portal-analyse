import queue
import time

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from stt.LLMBridge import LLMBridge
from tools.desktop import CURRENT_MODEL


class SummaryWorker(QObject):
    summary_ready = pyqtSignal(list)
    status_update = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    task_completed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.task_queue = queue.Queue()
        self.is_running = True
        self.llm = None

        self._initialize_llm()

    @pyqtSlot()
    def run_forever(self):
        """Dauerhaft laufender Worker"""
        self.status_update.emit("LLM-Thread gestartet")

        while self.is_running:
            try:
                # Warte auf Aufgaben (mit Timeout)
                try:
                    task = self.task_queue.get(timeout=0.1)  # 100ms Timeout

                    if task.get("type") == "SUMMARIZE":
                        self._process_transcription(task)
                    elif task.get("type") == "STOP_WORKER":
                        break

                    self.task_queue.task_done()

                except queue.Empty:
                    # Keine Aufgaben vorhanden, weiterlaufen.
                    pass

            except Exception as e:
                self.error_occurred.emit(f"Interner Fehler im LLM-Bridge-Worker: {str(e)}")

    def add_transcription_task(self, transcript, task_id=None):
        """Füge eine Transkriptionsaufgabe zur Warteschlange hinzu"""
        if not task_id:
            task_id = str(time.time())  # Eindeutige ID generieren

        task = {
            "type": "SUMMARIZE",
            "transcript": transcript,
            "task_id": task_id
        }
        self.task_queue.put(task)
        self.status_update.emit(f"LLM-Aufgabe hinzugefügt (Task: {task_id})")

    def stop_worker(self):
        """Stoppe den Worker ordentlich"""
        self.is_running = False
        self.task_queue.put({"type": "STOP_WORKER"})

    # Kompatibilität mit altem Interface
    def stop(self):
        self.stop_worker()

    def _initialize_llm(self):
        """Initialisiere die LLM-Bridge"""
        try:
            self.llm = LLMBridge()
            self.llm.set_model(CURRENT_MODEL)

            self.status_update.emit("LLM geladen")
        except Exception as e:
            self.error_occurred.emit(f"Fehler beim Laden des LLM: {str(e)}")

    def _process_transcription(self, task):
        if not self.llm:
            self.error_occurred.emit("LLM nicht verfügbar")
            return

        transcript = task.get("transcript")
        task_id = task.get("task_id", "unknown")

        if not transcript:
            self.error_occurred.emit("Kein Text zum Zusammenfassen vorhanden")
            self.task_completed.emit()
            return

        try:
            self.status_update.emit(f"Starte Zusammenfassung (Task: {task_id})")


            # TODO: Eigentliche Zusammenfassung durchführen
            result = self.llm.process_transcript(transcript)

            # Ergebnis senden
            self.summary_ready.emit(result)
            self.status_update.emit(f"Zusammenfassung abgeschlossen (Task: {task_id})")
            self.task_completed.emit()

        except Exception as e:
            error_msg = f"LLM-Fehler (Task: {task_id}): {str(e)}"
            self.task_completed.emit()
            self.error_occurred.emit(error_msg)