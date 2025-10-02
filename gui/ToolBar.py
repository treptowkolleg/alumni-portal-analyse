import math

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import QToolBar, QWidget, QHBoxLayout, QProgressBar, QLabel, QVBoxLayout

from tools.desktop import get_rel_path, ICON_PATH
from vad.VoiceActivityDetector import MAX_SILENCE_SAMPLES


class ToolBar(QToolBar):

    def __init__(self, parent=None):
        self.target_value = 0
        self.current_value = 0

        super(ToolBar, self).__init__(parent)

        self.start_action = QAction(QIcon(get_rel_path(ICON_PATH, "player-record.svg")), None, self)
        self.start_action.setStatusTip("Aufnahme starten")
        self.start_action.setShortcut("R")


        self.stop_action = QAction(QIcon(get_rel_path(ICON_PATH, "player-stop.svg")), None, self)
        self.stop_action.setDisabled(True)
        self.stop_action.setStatusTip("Aufnahme stoppen")
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

        self.addSeparator()

        self.time_out_bar = QProgressBar(self)
        self.time_out_bar.setRange(0, MAX_SILENCE_SAMPLES)
        self.time_out_bar.setValue(MAX_SILENCE_SAMPLES)
        self.time_out_bar.setTextVisible(False)
        self.time_out_bar.setStatusTip("Timeout bis zur nächsten Transkription")

        self.time_out_bar.setStyleSheet("""
        QProgressBar 
        {
            background-color: rgba(41,74,112,120);
            border-radius: 2px;
            height: 8px;
            border: none;
        }
        QProgressBar::chunk 
        {
            background-color: rgba(41,74,112,200);
            border-radius: 2px;
            border: none;
            padding: 2px;
            margin: 4px;
        }      
        """)

        self.volume_bar = QProgressBar(self)
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setValue(0)
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setStatusTip("Lautstärke")

        self.volume_bar.setStyleSheet("""
                QProgressBar 
                {
                    background-color: rgba(52,122,89,120);
                    border-radius: 2px;
                    height: 8px;
                    border: none;
                }
                QProgressBar::chunk 
                {
                    
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #7DCEA0, stop: 1 #27AE60);
    
                    transition: width 0.2s ease-in-out; 
                    border-radius: 2px;
                    border: none;
                    padding: 2px;
                    margin: 4px;
                }      
                """)

        volume_container = QWidget()
        volume_container.setMinimumWidth(100)
        volume_container.setMaximumWidth(300)
        volume_container_layout = QVBoxLayout(volume_container)
        volume_container_layout.setContentsMargins(5, 5, 0, 5)
        volume_container_layout.setSpacing(5)
        volume_container_layout.addWidget(QLabel("Lautstärke"))
        volume_container_layout.addWidget(self.volume_bar)
        self.addWidget(volume_container)

        self.addSeparator()

        time_out_container = QWidget()
        container_layout = QVBoxLayout(time_out_container)
        container_layout.setContentsMargins(5,5,0,5)
        container_layout.setSpacing(5)
        container_layout.addWidget(QLabel("Transkription Timeout"))
        container_layout.addWidget(self.time_out_bar)
        self.addWidget(time_out_container)

        self.addSeparator()



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
                    background-color: rgba(41,74,112,255);
                     border-radius: 4px;
                    padding: 6px;
                    margin: 2px;
                }
                """)

        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_volume)
        self.animation_timer.start(30)

    def update_timeout(self, samples):
            if samples <= MAX_SILENCE_SAMPLES:
                self.time_out_bar.setValue(MAX_SILENCE_SAMPLES - samples)
            else:
                self.reset_timeout()

    def animate_volume(self):
        """Flüssige Animation zum Zielwert"""
        if abs(self.target_value - self.current_value) > 1:
            # Langsame Annäherung (wie CSS transition)
            self.current_value += (self.target_value - self.current_value) * .1
            cur_val = int(self.current_value)
            if cur_val > 0:
                self.volume_bar.setValue(cur_val)
            else:
                self.volume_bar.setValue(0)

    def update_volume(self, rms):
        if rms > 0:
            volume_db = 20 * math.log10(rms)
            volume_percent = max(0, min(100, int((volume_db + 60) * 1.67)))
        else:
            volume_percent = 0
        self.target_value = volume_percent

    def reset_timeout(self):
        self.time_out_bar.setValue(MAX_SILENCE_SAMPLES)

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
