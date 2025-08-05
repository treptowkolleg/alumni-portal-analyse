from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QToolBar

from tools.desktop import get_rel_path, ICON_PATH


class ToolBar(QToolBar):

    def __init__(self, parent=None):
        super(ToolBar, self).__init__(parent)

        start_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/player-play.svg")), None, self)
        start_action.setStatusTip("Transkription starten")
        # start_action.triggered.connect(self.start_transcription)

        stop_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/player-stop.svg")), None, self)
        stop_action.setDisabled(True)
        stop_action.setStatusTip("Transkription stoppen")
        # stop_action.triggered.connect(self.stop_transcription)

        save_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/device-floppy.svg")), None, self)
        save_action.setDisabled(True)
        save_action.setStatusTip("Protokoll speichern")
        # save_action.triggered.connect(self.save_protocol)

        self.addAction(start_action)
        self.addAction(stop_action)
        self.addAction(save_action)