from PyQt6.QtWidgets import QStyledItemDelegate

class AlignDelegate(QStyledItemDelegate):
    def __init__(self, alignment, parent=None):
        super().__init__(parent)
        self.alignment = alignment

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = self.alignment