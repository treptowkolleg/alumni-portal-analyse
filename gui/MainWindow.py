from PyQt6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt6.QtWidgets import QMainWindow, QLabel, QTableView, \
    QWidget, QHeaderView, QVBoxLayout
from PyQt6.QtCore import Qt

from gui.MenuBar import MenuBar
from gui.StatusBar import StatusBar
from gui.ToolBar import ToolBar
from tools.desktop import get_min_size, get_rel_path, ICON_PATH, WINDOW_TITLE, WINDOW_ICON, WINDOW_RATIO


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon(get_rel_path(ICON_PATH,WINDOW_ICON)))
        self.setMinimumSize(*get_min_size(WINDOW_RATIO))
        # Komponenten initialisieren
        self.menubar = None
        self.init_menu()
        self.init_status_bar()
        self.init_toolbar()
        self.add_layout()

    def init_menu(self):
        self.menubar = MenuBar(self)
        self.setMenuBar(self.menubar)


    def init_status_bar(self):
        self.setStatusBar(StatusBar(self))


    def init_toolbar(self):
        toolbar = ToolBar("Aufnahmesteuerung")
        toolbar.setObjectName("toolbar_1")
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)
        self.menubar.add_toolbar(toolbar)


    def add_layout(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        table = QTableView()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["ID", "Text"])

        # Beispiel-Daten hinzufügen
        daten = [
            ["0", "Herzlich willkommen zur Schulkonferenz. Ich freue mich, dass alle da sin."],
            ["1", "Wir sprechen heute über die Raucherecke, die uns aktuell noch ein paar Probleme bereitet."],
        ]

        for zeile in daten:
            items = [QStandardItem(eintrag) for eintrag in zeile]
            items[0].setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            model.appendRow(items)

        # Modell mit Tabelle verbinden
        table.setModel(model)

        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)


        # Fenster anzeigen
        table_titel = QLabel("Erfasste Transkription")
        font = table_titel.font()
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Bold)
        table_titel.setFont(font)
        layout.addWidget(table_titel)
        layout.addWidget(table)
