from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import QTableView


class TableView(QTableView):
    def __init__(self, header_labels: list, parent=None):
        super(TableView, self).__init__(parent)
        self.model = QStandardItemModel()
        self.set_model(header_labels)

    def set_model(self, header_labels: list):
        self.model.setHorizontalHeaderLabels(header_labels)
        self.setModel(self.model)
