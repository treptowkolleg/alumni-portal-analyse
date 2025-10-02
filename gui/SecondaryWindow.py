import markdown
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QTextEdit

from tools.desktop import get_rel_path, ICON_PATH, WINDOW_ICON


class SecondaryWindow(QMainWindow):
    window_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Zusammenfassung")
        self.setWindowIcon(QIcon(get_rel_path(ICON_PATH, WINDOW_ICON)))
        self.setMinimumSize(300, 720)
        self.resize(480, 720)

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.web_view = QTextEdit()
        self.web_view.setHtml("""
                    <html>
                        <body>
                            <i>Markdown-Inhalt wird hier angezeigt...</i>
                        </body>
                    </html>
                """)

        self.setCentralWidget(self.web_view)

    def update_from_markdown(self, markdown_text):
        """Aktualisiert die Anzeige mit Markdown-Inhalt"""
        # Markdown → HTML

        text = markdown_text.get("summary", "Kein Text vorhanden")
        title = markdown_text.get("title", "Kein Titel vorhanden")

        html_content = markdown.markdown(text)

        # Optional: CSS für bessere Darstellung
        full_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 12px;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #FFFFFF;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            {html_content}
        </body>
        </html>
        """
        self.web_view.setHtml(full_html)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F5:
            self.window_closed.emit()

    def closeEvent(self, event):
        # Verhindere, dass das Fenster zerstört wird
        event.ignore()  # Fenster wird nicht geschlossen
        self.window_closed.emit()  # Nur verstecken