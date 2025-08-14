from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout

from tools.desktop import get_rel_path, ICON_PATH


class ToolBar(QToolBar):

    def __init__(self, parent=None):
        super(ToolBar, self).__init__(parent)

        self.start_action = QAction(QIcon(get_rel_path(ICON_PATH, "player-record.svg")), None, self)
        self.start_action.setStatusTip("Transkription starten")
        self.start_action.setShortcut("R")


        self.stop_action = QAction(QIcon(get_rel_path(ICON_PATH, "player-stop.svg")), None, self)
        self.stop_action.setDisabled(True)
        self.stop_action.setStatusTip("Transkription stoppen")
        self.stop_action.setShortcut("F")

        self.rec_state_action = QSvgWidget(get_rel_path(ICON_PATH, "microphone-off.svg"), self)
        self.rec_state_action.setStyleSheet("""
        QSvgWidget {
        }
        """)
        self.rec_state_action.setFixedSize(24,24)

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

        self.speech_detected = False

        tool_button = self.widgetForAction(self.start_action)
        if tool_button:
            # Setze die benutzerdefinierte Eigenschaft direkt am Widget
            tool_button.setProperty("dataName", "rec")

        tool_button2 = self.widgetForAction(self.stop_action)
        if tool_button2:
            # Setze die benutzerdefinierte Eigenschaft direkt am Widget
            tool_button2.setProperty("dataName", "stop")

        self.setStyleSheet("""
                QToolButton[dataName="rec"] {
                    background-color: rgba(255, 59, 48,40);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QToolButton[dataName="rec"]:hover {
                    background-color: rgba(255, 59, 48,120);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QToolButton[dataName="rec"]:pressed {
                    background-color: rgba(255, 59, 48,100);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QToolButton[dataName="rec"]:disabled {
                    background-color: rgba(255, 59, 48,200);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                
                QToolButton[dataName="stop"] {
                    background-color: rgba(41,74,112,80);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QToolButton[dataName="stop"]:hover {
                    background-color: rgba(41,74,112,120);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QToolButton[dataName="stop"]:pressed {
                    background-color: rgba(41,74,112,100);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                QToolButton[dataName="stop"]:disabled {
                    background-color: rgba(41,74,112,200);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                """)



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
