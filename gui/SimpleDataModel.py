from PyQt6.QtCore import QAbstractTableModel


class SimpleTableModel(QAbstractTableModel):
    def __init__(self, data=None, headers=None, parent=None):
        super().__init__(parent)
        self._data = data or [
            ["Alice", 30, "Entwicklerin"],
            ["Bob",   25, "Designer"],
            ["Caro",  28, "Managerin"]
        ]
        self._headers = headers or ["Name", "Alter", "Beruf"]