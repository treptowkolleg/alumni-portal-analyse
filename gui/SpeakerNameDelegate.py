from PyQt6.QtWidgets import QStyledItemDelegate


class SpeakerNameDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        # Optional: Spezielle Behandlung
        return editor
