from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout

from tools.desktop import get_rel_path, ICON_PATH


class ToolBar(QToolBar):

    def __init__(self, parent=None):
        super(ToolBar, self).__init__(parent)

        self.start_action = QAction(QIcon(get_rel_path(ICON_PATH, "player-record.svg")), None, self)
        self.start_action.setStatusTip("Transkription starten")

        self.stop_action = QAction(QIcon(get_rel_path(ICON_PATH, "player-stop.svg")), None, self)
        self.stop_action.setDisabled(True)
        self.stop_action.setStatusTip("Transkription stoppen")

        self.rec_state_action = QSvgWidget(get_rel_path(ICON_PATH, "microphone-off.svg"), self)
        self.rec_state_action.setFixedSize(20, 20)
        self.rec_state_action.setStatusTip("Sprachaktivität")


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

        self.speech_detected = False

    def on_speech_detected(self):
        if not self.speech_detected:
            self.speech_detected = True
            self.rec_state_action.load(get_rel_path(ICON_PATH, "microphone.svg"))

    def on_speech_lost(self):
        if self.speech_detected:
            self.speech_detected = False
            self.rec_state_action.load(get_rel_path(ICON_PATH, "microphone-off.svg"))

    def stop_recording(self):
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.speech_detected = False
        self.rec_state_action.load(get_rel_path(ICON_PATH, "microphone-off.svg"))

    def start_recording(self):
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(True)
