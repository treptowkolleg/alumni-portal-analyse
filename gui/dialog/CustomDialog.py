from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QFormLayout, QLineEdit, QComboBox


class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Profil-Training")
        self.setMinimumSize(640, 480)

        self.label = QLabel("Trainiere dein Profil..")

        layout = QFormLayout()

        # Mit Label-Widgets
        layout.addRow(QLabel("Benutzername:"), QLineEdit())
        layout.addRow(QLabel("Passwort:"), QLineEdit())
        layout.addRow(QLabel("Rolle:"), QComboBox())

        # Breite Zeile für Button
        button = QPushButton("Login")
        button.clicked.connect(self.accept)
        layout.addRow(button)

        self.setLayout(layout)
