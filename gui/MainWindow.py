from functools import partial

from PyQt6.QtCore import Qt, QThread, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout

from gui.MenuBar import MenuBar
from gui.SpeakerTableView import SpeakerTable
from gui.StatusBar import StatusBar
from gui.ToolBar import ToolBar
from gui.TranscriptDataManager import TranscriptDataManager
from gui.TranscriptTableView import TranscriptTable
from gui.widget.CheckboxAction import CheckboxAction
from stt.SummaryWorker import SummaryWorker
from tools.desktop import get_min_size, get_rel_path, ICON_PATH, WINDOW_TITLE, WINDOW_ICON, WINDOW_RATIO, \
    WHISPER_SPEAKER_RULE
from vad.RecorderWorker import RecorderWorker
from vad.TranscriberWorker import TranscriberWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.transcriber_worker = None
        self.transcriber_thread = None
        self.recorder_worker = None
        self.recorder_thread = None
        self.llm_worker = None
        self.llm_thread = None

        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(get_rel_path(ICON_PATH, WINDOW_ICON)))
        self.setMinimumSize(*get_min_size(WINDOW_RATIO))

        # Tabelle vorbereiten
        self.data_manager = TranscriptDataManager()
        self.transcript_table = TranscriptTable(self.data_manager)
        self.speaker_table = SpeakerTable(self.data_manager)

        self.transcript_table.speakerChanged.connect(self.on_speaker_changed)
        self.speaker_table.speakerNameChanged.connect(self.on_speaker_name_changed_in_speaker_table)

        self.toolbar = ToolBar("Aufnahmesteuerung")

        # Komponenten initialisieren
        self.menubar = MenuBar(self)
        self.init_menu()
        self.init_status_bar()
        self.init_toolbar()
        self.add_layout()
        self.setup_recorder()
        self.setup_transcriber()
        self.setup_llm()

        self.toolbar.start_action.triggered.connect(self.start_recording)
        self.toolbar.stop_action.triggered.connect(self.stop_recording)

        whisper_option: dict[str, str] = {
            "streng": "conservative",
            "ausgewogen": "balanced",
            "locker": "liberal",
        }

        self.menubar.settings_menu.addSeparator()
        whisper_header = QAction(QIcon(get_rel_path(ICON_PATH, "activity-heartbeat.svg")), "Ermittlung der Sprecher",
                                 self.menubar.settings_menu)
        whisper_header.setEnabled(False)
        self.menubar.settings_menu.addAction(whisper_header)

        for name, value in whisper_option.items():
            whisper_action = CheckboxAction(text=name,
                                            action=partial(self.transcriber_worker.transcriber.set_preset, value),
                                            parent=self)
            self.menubar.action_group_whisper.addAction(whisper_action)
            self.menubar.settings_menu.addAction(whisper_action)
            if value == WHISPER_SPEAKER_RULE:
                whisper_action.setChecked(True)

    def on_speaker_changed(self, idn, new_speaker):
        # Aktualisiere das Segment im DataManager
        self.speaker_table.update_speaker_for_id(idn, new_speaker)
        print(f"DEBUG: {idn} -> {new_speaker}")

    def on_speaker_name_changed_in_speaker_table(self, old_speaker, new_speaker, affected_ids):
        # Aktualisiere TranscriptTable
        self.transcript_table.update_speaker_for_ids(affected_ids, new_speaker)

    def init_menu(self):
        self.setMenuBar(self.menubar)

    def init_status_bar(self):
        self.setStatusBar(StatusBar(self))

    def init_toolbar(self):
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.toolbar)
        self.menubar.add_toolbar(self.toolbar)

    def add_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_layout = QHBoxLayout()
        central_widget.setLayout(central_layout)

        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        table_widget = QWidget()
        table_layout = QVBoxLayout()
        table_widget.setLayout(table_layout)

        speaker_table_widget = QWidget()
        speaker_table_layout = QVBoxLayout()
        speaker_table_widget.setLayout(speaker_table_layout)

        # Fenster anzeigen

        table_layout.addWidget(self.transcript_table)
        table_layout.setContentsMargins(0, 0, 0, 0)

        speaker_table_layout.addWidget(self.speaker_table)
        speaker_table_layout.setContentsMargins(0, 0, 0, 0)

        main_layout.addWidget(speaker_table_widget, 3)
        main_layout.addWidget(table_widget, 8)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        central_layout.addWidget(main_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)

    def setup_recorder(self):
        self.recorder_thread = QThread()
        self.recorder_worker = RecorderWorker()

        self.recorder_worker.moveToThread(self.recorder_thread)

        # Signale verbinden
        self.recorder_thread.started.connect(self.recorder_worker.run_forever)
        self.recorder_worker.speech_detected.connect(self.on_speech_detected)
        self.recorder_worker.speech_lost.connect(self.on_speech_lost)
        self.recorder_worker.recording_done.connect(self.on_recording_done)
        self.recorder_worker.status_update.connect(self.update_recorder_status)
        self.recorder_worker.error_occurred.connect(self.handle_recorder_error)

        self.recorder_thread.start()

    def setup_transcriber(self):
        self.transcriber_thread = QThread()
        self.transcriber_worker = TranscriberWorker()

        self.transcriber_worker.moveToThread(self.transcriber_thread)

        # Signale verbinden
        self.transcriber_thread.started.connect(self.transcriber_worker.run_forever)
        self.transcriber_worker.transcription_ready.connect(self.on_transcription_ready)
        self.transcriber_worker.status_update.connect(self.update_transcriber_status)
        self.transcriber_worker.error_occurred.connect(self.handle_transcriber_error)
        self.transcriber_worker.task_completed.connect(self.on_transcription_task_completed)

        self.transcriber_worker.progress_update.connect(self.update_progress)

        self.transcriber_thread.start()

    def setup_llm(self):
        self.llm_thread = QThread()
        self.llm_worker = SummaryWorker()

        self.llm_worker.moveToThread(self.llm_thread)

        # Signale verbinden
        self.llm_thread.started.connect(self.llm_worker.run_forever)
        self.llm_worker.status_update.connect(self.update_llm_status)
        self.llm_worker.error_occurred.connect(self.handle_recorder_error)

        self.llm_thread.start()

    def on_speech_detected(self):
        if self.recorder_worker.is_recording_active is True:
            self.toolbar.on_speech_detected()
        else:
            self.toolbar.on_speech_lost()

    def on_speech_lost(self):
        self.toolbar.on_speech_lost()

    def on_recording_done(self, recording):
        """Wird aufgerufen, wenn eine Aufnahme fertig ist"""
        # Füge Transkriptionsaufgabe hinzu
        self.transcriber_worker.add_transcription_task(recording)

    def on_transcription_ready(self, result):
        """Wird aufgerufen, wenn Transkription fertig ist"""
        self.transcript_table.update_transcript_table(result)
        self.speaker_table.update_table(result)

    def on_segment_speaker_changed(self, segment_id, new_speaker):
        """Wird aufgerufen, wenn ein Sprecher für eine Segment-ID geändert wird"""
        # Sprecher im Datenmanager aktualisieren
        self.data_manager.update_segment_speaker(segment_id, new_speaker)
        # Beide Tabellen werden automatisch über dataUpdated-Signal aktualisiert

    def on_transcription_task_completed(self):
        QTimer.singleShot(1000, lambda: self.show_transcription_progress(False))

    def update_recorder_status(self, status):
        print(f"Recorder-Status: {status}")

    def update_llm_status(self, status):
        print(f"LLM-Status: {status}")

    def update_transcriber_status(self, status):
        print(f"Transcriber-Status: {status}")

    def show_transcription_progress(self, show=True):
        """Zeige/Verstecke Fortschrittsanzeige"""
        if show:
            self.statusBar().status_label.setText("Transkription läuft...")
            self.statusBar().progress_bar.setRange(0, 0)  # Unbestimmter Fortschritt
        else:
            self.statusBar().status_label.setText("Bereit")
            self.statusBar().progress_bar.setRange(0, 100)

    def update_progress(self, value, maximum=100):
        """Aktualisiere Fortschritt (0-100)"""
        if maximum > 0:
            self.statusBar().progress_bar.setRange(0, 0)
            self.statusBar().status_label.setText(f"Transkription")

    def handle_recorder_error(self, e):
        print(f"Recorder-Error: {e}")

    def handle_transcriber_error(self, e):
        print(f"Transcriber-Error: {e}")

    def start_recording(self):
        """Starte Aufnahme (falls benötigt)"""
        self.toolbar.start_recording()
        self.recorder_worker.start_recording()

    def stop_recording(self):
        """Stoppe Aufnahme"""
        self.recorder_worker.stop_recording()
        self.toolbar.stop_recording()

    def closeEvent(self, event):
        """Wird aufgerufen, wenn das Fenster geschlossen wird"""
        print("Anwendung wird beendet - räume auf...")

        # Stoppe Aufnahme, falls aktiv
        try:
            self.stop_recording()
        except:
            pass

        # Worker stoppen
        try:
            if self.recorder_worker:
                self.recorder_worker.stop_worker()
        except:
            pass

        try:
            if self.transcriber_worker:
                self.transcriber_worker.stop_worker()
        except:
            pass

        try:
            if self.llm_worker:
                self.llm_worker.stop_worker()
        except:
            pass

        # Threads beenden (mit Timeout)
        try:
            if self.recorder_thread:
                self.recorder_thread.quit()
                self.recorder_thread.wait(1000)
        except:
            pass

        try:
            if self.transcriber_thread:
                self.transcriber_thread.quit()
                self.transcriber_thread.wait(1000)
        except:
            pass

        try:
            if self.llm_thread:
                self.llm_thread.quit()
                self.llm_thread.wait(1000)
        except:
            pass

        print("Aufräumen abgeschlossen")
        event.accept()

    def cleanup(self):
        """Beim Beenden aufräumen"""
        self.recorder_worker.stop_worker()
        self.recorder_thread.quit()
        self.recorder_thread.wait()

        self.transcriber_worker.stop_worker()
        self.transcriber_thread.quit()
        self.transcriber_thread.wait()

        self.llm_worker.stop_worker()
        self.llm_thread.quit()
        self.llm_thread.wait()
