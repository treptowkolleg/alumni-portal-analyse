from PyQt6.QtCore import QThread, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout

from tools.desktop import get_rel_path, ICON_PATH
from vad.AudioTranscriber import AudioTranscriber
from vad.RecorderWorker import RecorderWorker


class ToolBar(QToolBar):

    def __init__(self, parent=None):
        super(ToolBar, self).__init__(parent)

        self.worker = None
        self.thread = None
        self.transcriber = AudioTranscriber()

        self.start_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/player-play.svg")), None, self)
        self.start_action.setStatusTip("Transkription starten")
        self.start_action.triggered.connect(self.recording_aimed)

        self.stop_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/player-stop.svg")), None, self)
        self.stop_action.setDisabled(True)
        self.stop_action.setStatusTip("Transkription stoppen")
        self.stop_action.triggered.connect(self.stop_recording)

        self.rec_state_action = QSvgWidget(get_rel_path(ICON_PATH, "outline/microphone-off.svg"), self)
        self.rec_state_action.setFixedSize(20, 20)
        self.rec_state_action.setStatusTip("Sprachaktivität")

        save_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/device-floppy.svg")), None, self)
        save_action.setDisabled(True)
        save_action.setStatusTip("Protokoll speichern")
        # save_action.triggered.connect(self.save_protocol)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)  # links, oben, rechts, unten
        layout.addWidget(self.rec_state_action)

        self.addSeparator()
        self.addWidget(container)
        self.addSeparator()
        self.addAction(self.start_action)
        self.addAction(self.stop_action)
        self.addSeparator()

    def on_recording_stopped(self):
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.rec_state_action.load(get_rel_path(ICON_PATH, "outline/microphone-off.svg"))
        self.transcriber.id_count = 0
        print("⏹️ \tGestoppt")

    def on_speech_detected(self):
        self.rec_state_action.load(get_rel_path(ICON_PATH, "outline/microphone.svg"))

    def on_speech_lost(self):
        self.rec_state_action.load(get_rel_path(ICON_PATH, "outline/microphone-off.svg"))

    def stop_recording(self):
        if self.worker:
            self.worker.is_stopped = True
            self.worker.is_running = False

    def recording_aimed(self):
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(True)

        self.thread = QThread()
        self.worker = RecorderWorker()
        self.worker.moveToThread(self.thread)

        # Verbindungen
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.started.connect(lambda: print("▶️ Aufnahme gestartet"))
        self.worker.speech_detected.connect(self.on_speech_detected)
        self.worker.speech_lost.connect(self.on_speech_lost)
        self.worker.recording_done.connect(self.transcriber.process_recording, Qt.ConnectionType.QueuedConnection)
        self.worker.finished.connect(self.on_recording_stopped)

        self.thread.start()
