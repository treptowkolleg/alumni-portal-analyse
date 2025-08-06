from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QStyleFactory
from py3nvml import py3nvml as nvml

from gui.MainWindow import MainWindow
from tools.desktop import WINDOW_STYLE

"""
Grafische Anwendung einrichten
"""
app = QApplication([])
app.setStyle(QStyleFactory.create(WINDOW_STYLE))
app.styleHints().setColorScheme(Qt.ColorScheme.Dark)

# Hauptfenster deklarieren und App starten
nvml.nvmlInit()
window = MainWindow()
window.show()
app.exec()
nvml.nvmlShutdown()
