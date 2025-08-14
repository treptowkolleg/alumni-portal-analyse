from functools import partial

from PyQt6.QtGui import QAction, QIcon, QActionGroup, QKeySequence
from PyQt6.QtWidgets import QMenuBar, QMessageBox, QToolBar

from gui.dialog.CustomDialog import CustomDialog
from gui.widget.Action import Action
from gui.widget.CheckboxAction import CheckboxAction
from tools.desktop import WINDOW_TITLE, APP_VERSION, APP_DESCRIPTION, get_rel_path, ICON_PATH, MODELS, CURRENT_MODEL


def action_training():
    print("Training starten")


def print_action(text):
    print(text)


class MenuBar(QMenuBar):

    def __init__(self, parent=None):
        super(MenuBar, self).__init__(parent)

        self.dialog = CustomDialog(self.window())

        # Hauptmenü
        file_menu = self.addMenu("Datei")
        self.view_menu = self.addMenu("Ansicht")
        self.settings_menu = self.addMenu("Einstellungen")
        self.tools_menu = self.addMenu("Tools")
        help_menu = self.addMenu("Hilfe")

        exit_action = QAction(QIcon(get_rel_path(ICON_PATH, "power.svg")), "Beenden", self)
        exit_action.triggered.connect(parent.close)
        exit_action.setShortcut(QKeySequence.StandardKey.Close)
        self.btn_new_project = QAction(QIcon(get_rel_path(ICON_PATH, "file-plus.svg")), "Neues Projekt", self)
        self.btn_new_project.setShortcut(QKeySequence.StandardKey.New)
        self.btn_demo_data = QAction(QIcon(get_rel_path(ICON_PATH, "test-pipe.svg")), "Demonstration laden", self)

        file_menu.addAction(self.btn_new_project)
        file_menu.addAction(self.btn_demo_data)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        action_group = QActionGroup(self.settings_menu)
        action_group.setExclusive(True)

        self.settings_menu.addSeparator()
        header = QAction(QIcon(get_rel_path(ICON_PATH, "ai.svg")), "LLM", self.settings_menu)
        header.setEnabled(False)
        self.settings_menu.addAction(header)

        # TODO: In MainWindow verschieben und mit LLM-Worker verknüpfen
        for name, model in MODELS.items():
            action = CheckboxAction(text=name, action=partial(print_action, model), parent=self)
            action_group.addAction(action)
            self.settings_menu.addAction(action)
            if model == CURRENT_MODEL:
                action.setChecked(True)


        self.action_group_whisper = QActionGroup(self.settings_menu)
        self.action_group_whisper.setExclusive(True)

        self.settings_menu.addSeparator()
        header = QAction(QIcon(get_rel_path(ICON_PATH, "settings.svg")), "Spezialfunktionen",
                         self.settings_menu)
        header.setEnabled(False)
        self.settings_menu.addAction(header)

        self.settings_menu.addAction(CheckboxAction(None, "Turbomodus", parent=self))
        training_action = Action("treadmill", "Trainieren", action_training, self)
        training_action.triggered.connect(self.show_training_dialog)
        training_action.setShortcut("F8")
        self.tools_menu.addAction(training_action)

        self.view_menu.addSeparator()
        header = QAction(QIcon(get_rel_path(ICON_PATH, "tools.svg")), "Werkzeugleisten", self.view_menu)
        header.setEnabled(False)
        self.view_menu.addAction(header)

        about_action = QAction(QIcon(get_rel_path(ICON_PATH, "question-mark.svg")), "Über", self)
        about_action.triggered.connect(self.show_about_dialog)
        about_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_menu.addAction(about_action)

    def add_toolbar(self, toolbar: QToolBar):
        action = QAction(toolbar.windowTitle(), self)
        action.setCheckable(True)
        action.setChecked(True)
        action.setShortcut("Alt+R")
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

    def show_training_dialog(self):
        self.dialog.exec()
