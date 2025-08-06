from PyQt6.QtGui import QAction, QIcon

from tools.desktop import get_rel_path, ICON_PATH


class Action(QAction):
    def __init__(self, icon=None, text=None, action=None, parent=None):
        super().__init__(parent)

        if icon is not None:
            self.setIcon(QIcon(get_rel_path(ICON_PATH, f"outline/{icon}.svg")))

        if text is not None:
            self.setText(text)
            self.setIconText(text)

        if action is not None:
            self.triggered.connect(action)
