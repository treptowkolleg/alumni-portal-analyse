from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt6.QtWidgets import QMainWindow, QLabel, QTableView, \
    QWidget, QHeaderView, QVBoxLayout

from gui.MenuBar import MenuBar
from gui.StatusBar import StatusBar
from gui.ToolBar import ToolBar
from tools.desktop import get_min_size, get_rel_path, ICON_PATH, WINDOW_TITLE, WINDOW_ICON, WINDOW_RATIO


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(get_rel_path(ICON_PATH, WINDOW_ICON)))
        self.setMinimumSize(*get_min_size(WINDOW_RATIO))

        self.toolbar = ToolBar("Aufnahmesteuerung")
        self.toolbar.transcriber.transcription_ready.connect(self.update_transcript_table)

        # Tabelle vorbereiten
        self.table = QTableView()

        # Model vorbereiten
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Id", "Text", "Start", "Ende"])
        self.table.setModel(self.model)

        self.configure_column_widths()

        # Komponenten initialisieren
        self.menubar = None
        self.init_menu()
        self.init_status_bar()
        self.init_toolbar()
        self.add_layout()

    def configure_column_widths(self):
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.table.resizeColumnsToContents()

        if self.table.columnWidth(0) < 60:
            self.table.setColumnWidth(0, 60)
        if self.table.columnWidth(2) < 60:
            self.table.setColumnWidth(2, 60)
        if self.table.columnWidth(3) < 60:
            self.table.setColumnWidth(3, 60)

    def init_menu(self):
        self.menubar = MenuBar(self)
        self.setMenuBar(self.menubar)

    def init_status_bar(self):
        self.setStatusBar(StatusBar(self))

    def init_toolbar(self):
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.toolbar)
        self.menubar.add_toolbar(self.toolbar)

    def update_transcript_table(self, segments):

        for seg in segments:
            text_id = QStandardItem(str(seg["id"]))
            start = QStandardItem(str(seg["start"]))
            end = QStandardItem(str(seg["end"]))
            text = QStandardItem(seg["text"])
            self.model.appendRow([text_id, text, start, end])

        self.configure_column_widths()

    def add_layout(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Fenster anzeigen
        table_titel = QLabel("Erfasste Transkription")
        font = table_titel.font()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Bold)
        table_titel.setFont(font)
        layout.addWidget(table_titel)
        layout.addWidget(self.table)
