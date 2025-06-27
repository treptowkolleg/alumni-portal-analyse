from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog, QLabel, QProgressBar, QSlider
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, Qt


class AudioPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Mediaplayer")
        self.setMinimumWidth(400)
        self.setFixedHeight(400)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # UI
        layout = QVBoxLayout()
        self.media_label = QLabel("Titel")
        self.button_open = QPushButton("Datei öffnen")
        self.button_play = QPushButton("Abspielen")
        self.button_play.setDisabled(True)
        self.button_stop = QPushButton("Stop")
        self.button_stop.setDisabled(True)
        self.button_detach = QPushButton("Auswerfen")
        self.button_detach.setDisabled(True)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)

        self.button_open.clicked.connect(self.open_file)
        self.button_play.clicked.connect(self.toggle)
        self.button_stop.clicked.connect(self.stop)
        self.button_detach.clicked.connect(self.detach_source)
        self.player.durationChanged.connect(lambda d: self.init_progress_bar(d))
        self.player.positionChanged.connect(lambda p: self.update_progress_bar(p))


        layout.addWidget(self.media_label)
        layout.addWidget(self.button_open)
        layout.addWidget(self.button_detach)
        layout.addWidget(self.button_play)
        layout.addWidget(self.button_stop)
        layout.addWidget(self.slider)
        layout.addWidget(self.progress)
        self.setLayout(layout)

    def detach_source(self):
        self.stop()
        self.player.setSource(QUrl())
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.slider.setRange(0, 0)
        self.button_play.setDisabled(True)
        self.button_stop.setDisabled(True)
        self.button_detach.setDisabled(True)

    def init_progress_bar(self, duration):
        self.progress.setMaximum(duration)
        self.slider.setMaximum(duration)

    def update_progress_bar(self, pos):
        self.progress.setValue(pos)
        self.slider.setValue(pos)

    def toggle(self):
        if self.player.isPlaying():
            self.player.pause()
            self.button_play.setText("Abspielen")
        else:
            self.player.play()
            self.button_play.setText("Pause")
            self.button_stop.setDisabled(False)

    def stop(self):
        self.button_play.setText("Abspielen")
        self.button_stop.setDisabled(True)
        self.player.stop()

    def open_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Audio-Dateien (*.mp3 *.wav *.ogg)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.media_label.setText(self.player.source().fileName())
        if not self.player.source().isEmpty():
            self.button_play.setDisabled(False)
            self.button_stop.setDisabled(False)
            self.button_detach.setDisabled(False)
        else:
            self.button_play.setDisabled(True)
            self.button_stop.setDisabled(True)
            self.button_detach.setDisabled(True)



app = QApplication([])
window = AudioPlayer()
window.show()
app.exec()