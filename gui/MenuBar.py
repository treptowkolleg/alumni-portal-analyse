from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenuBar, QMessageBox, QToolBar

from tools.desktop import WINDOW_TITLE, APP_VERSION, APP_DESCRIPTION, get_rel_path, ICON_PATH


class MenuBar(QMenuBar):

    def __init__(self, parent=None):
        super(MenuBar, self).__init__(parent)

        # Hauptmenü
        file_menu = self.addMenu("Datei")
        self.view_menu = self.addMenu("Ansicht")
        help_menu = self.addMenu("Hilfe")

        exit_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/power.svg")),"Beenden", self)
        exit_action.triggered.connect(parent.close)
        file_menu.addAction(exit_action)

        self.view_menu.addSeparator()
        header = QAction(QIcon(get_rel_path(ICON_PATH, "outline/tools.svg")),"Werkzeugleisten", self.view_menu)
        header.setEnabled(False)
        self.view_menu.addAction(header)

        about_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/question-mark.svg")),"Über", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def add_toolbar(self, toolbar: QToolBar):

        action = QAction(toolbar.windowTitle(), self)
        action.setCheckable(True)
        action.setChecked(True)
        action.toggled.connect(toolbar.setVisible)
        toolbar.visibilityChanged.connect(action.setChecked)
        self.view_menu.addAction(action)

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "Über dieses Programm",
            f"<b>{WINDOW_TITLE}</b><br>Version {APP_VERSION}<br><br>© 2025 Benjamin Wagner, Sami Teuchert"
            f"{APP_DESCRIPTION}"
        )
