from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profil-Training")
        self.setMinimumSize(640,480)

        self.label = QLabel("Trainiere dein Profil..")
        self.button1 = QPushButton("Training starten")
        self.button2 = QPushButton("Abbrechen")

        self.button1.clicked.connect(self.accept)
        self.button2.clicked.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)

        self.setLayout(layout)