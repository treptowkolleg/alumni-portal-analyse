from PyQt6.QtWidgets import QStyledItemDelegate, QLineEdit


class SpeakerDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            editor.editingFinished.connect(lambda: self.commitData.emit(editor))
        return editor