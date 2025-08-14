import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication, QStyleFactory
from py3nvml import py3nvml as nvml

from gui.MainWindow import MainWindow
from tools.desktop import WINDOW_STYLE

"""
Grafische Anwendung einrichten
"""


def main():
    app = QApplication([])
    app.setStyle(QStyleFactory.create(WINDOW_STYLE))
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Highlight, QColor(41, 74, 112))
    app.setPalette(palette)

    # Hauptfenster deklarieren und App starten
    nvml.nvmlInit()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
