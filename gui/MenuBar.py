from functools import partial

from PyQt6.QtGui import QAction, QIcon, QActionGroup
from PyQt6.QtWidgets import QMenuBar, QMessageBox, QToolBar

from gui.dialog.CustomDialog import CustomDialog
from gui.widget.Action import Action
from gui.widget.CheckboxAction import CheckboxAction
from tools.desktop import WINDOW_TITLE, APP_VERSION, APP_DESCRIPTION, get_rel_path, ICON_PATH, MODELS


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

        exit_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/power.svg")), "Beenden", self)
        exit_action.triggered.connect(parent.close)
        file_menu.addAction(exit_action)

        action_group = QActionGroup(self.settings_menu)
        action_group.setExclusive(True)

        self.settings_menu.addSeparator()
        header = QAction(QIcon(get_rel_path(ICON_PATH, "outline/ai.svg")), "LLM", self.settings_menu)
        header.setEnabled(False)
        self.settings_menu.addAction(header)

        for name, model in MODELS.items():
            action = CheckboxAction(text=name, action=partial(print_action, model), parent=self)
            action_group.addAction(action)
            self.settings_menu.addAction(action)
            if name == "Gemma":
                action.selected = True

        self.settings_menu.addSeparator()
        whisper_header = QAction(QIcon(get_rel_path(ICON_PATH, "outline/ai.svg")), "Ermittlung der Sprecher", self.settings_menu)
        whisper_header.setEnabled(False)
        self.settings_menu.addAction(whisper_header)

        action_group_whisper = QActionGroup(self.settings_menu)
        action_group_whisper.setExclusive(True)

        whisper_option = {
            "konservativ" : "conservative",
            "ausgewogen" : "balanced",
            "liberal" : "liberal",
        }

        for name, setting in whisper_option.items():
            action = CheckboxAction(text=name, action=partial(print_action, setting), parent=self)
            action_group_whisper.addAction(action)
            self.settings_menu.addAction(action)
            if name == "ausgewogen":
                action.selected = True

        self.settings_menu.addSeparator()
        header = QAction(QIcon(get_rel_path(ICON_PATH, "outline/settings.svg")), "Spezialfunktionen",
                         self.settings_menu)
        header.setEnabled(False)
        self.settings_menu.addAction(header)

        self.settings_menu.addAction(CheckboxAction(None, "Turbomodus", parent=self))
        training_action = Action("treadmill", "Trainieren", action_training, self)
        training_action.triggered.connect(self.show_training_dialog)
        self.tools_menu.addAction(training_action)

        self.view_menu.addSeparator()
        header = QAction(QIcon(get_rel_path(ICON_PATH, "outline/tools.svg")), "Werkzeugleisten", self.view_menu)
        header.setEnabled(False)
        self.view_menu.addAction(header)

        about_action = QAction(QIcon(get_rel_path(ICON_PATH, "outline/question-mark.svg")), "Über", self)
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

    def show_training_dialog(self):
        self.dialog.exec()
