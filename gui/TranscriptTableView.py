from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QHeaderView

from gui.TableView import TableView


class TranscriptTable(TableView):
    def __init__(self, data_manager, parent=None):
        super(TranscriptTable, self).__init__(["Nr", "ID", "Sprecher", "Text", "Start", "Ende"], parent)
        self.data_manager = data_manager
        self.configure_column_widths()

    def configure_column_widths(self):
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.resizeColumnsToContents()

        if self.columnWidth(0) < 30:
            self.setColumnWidth(0, 30)
        if self.columnWidth(1) < 30:
            self.setColumnWidth(1, 30)
        if self.columnWidth(3) < 60:
            self.setColumnWidth(2, 60)
        if self.columnWidth(4) < 60:
            self.setColumnWidth(4, 60)
        if self.columnWidth(5) < 60:
            self.setColumnWidth(5, 60)

    def update_transcript_table(self, segments):
        for seg in segments:
            id = QStandardItem(str(seg["idn"]))
            text_id = QStandardItem(str(seg["id"]))
            speaker = QStandardItem(str(seg["speaker"]))
            start = QStandardItem(str(seg["start"]))
            end = QStandardItem(str(seg["end"]))
            text = QStandardItem(seg["text"])
            self.model.appendRow([id, text_id, speaker,  text, start, end])

        self.configure_column_widths()
