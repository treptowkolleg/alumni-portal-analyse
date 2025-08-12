import sys
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtWidgets import (
    QApplication, QTableView, QWidget, QHBoxLayout,
    QHeaderView, QAbstractItemView,
)

class SimpleTableModel(QAbstractTableModel):
    def __init__(self, data=None, headers=None, parent=None):
        super().__init__(parent)
        self._data = data or [
            ["Alice", 30, "Entwicklerin"],
            ["Bob",   25, "Designer"],
            ["Caro",  28, "Managerin"]
        ]
        self._headers = headers or ["Name", "Alter", "Beruf"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._data[0]) if self._data else 0

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return QVariant(self._data[index.row()][index.column()])
        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        if orientation == Qt.Orientation.Horizontal:
            return QVariant(self._headers[section])
        return QVariant(section + 1)

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEditable
        )

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        row, col = index.row(), index.column()
        # Beispiel‑Validierung: Spalte "Alter" muss int sein
        if col == 1:
            try:
                value = int(value)
            except ValueError:
                return False
        self._data[row][col] = value
        self.dataChanged.emit(index, index,
                              [Qt.ItemDataRole.DisplayRole,
                               Qt.ItemDataRole.EditRole])
        return True

def create_table_view(model):
    view = QTableView()
    view.setModel(model)
    view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    view.verticalHeader().setVisible(False)
    view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    view.setEditTriggers(
        QAbstractItemView.EditTrigger.DoubleClicked |
        QAbstractItemView.EditTrigger.SelectedClicked
    )
    return view

def main():
    app = QApplication(sys.argv)

    model = SimpleTableModel()

    view_a = create_table_view(model)
    view_b = create_table_view(model)

    win = QWidget()
    layout = QHBoxLayout(win)
    layout.addWidget(view_a)
    layout.addWidget(view_b)

    win.setWindowTitle("Synchronisierte QTableView‑Instanzen")
    win.resize(800, 300)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()