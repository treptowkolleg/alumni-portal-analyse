from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QHeaderView

from gui.TableView import TableView


class TranscriptTable(TableView):
    def __init__(self, parent=None):
        super(TranscriptTable, self).__init__(["#", "Sprecher", "Text", "Start", "Ende"], parent)
        self.configure_column_widths()

    def configure_column_widths(self):
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.resizeColumnsToContents()

        if self.columnWidth(0) < 30:
            self.setColumnWidth(0, 30)
        if self.columnWidth(3) < 60:
            self.setColumnWidth(3, 60)
        if self.columnWidth(4) < 60:
            self.setColumnWidth(4, 60)

    def update_transcript_table(self, segments):
        for seg in segments:
            text_id = QStandardItem(str(seg["id"]))
            speaker = QStandardItem(str(seg["speaker"]))
            start = QStandardItem(str(seg["start"]))
            end = QStandardItem(str(seg["end"]))
            text = QStandardItem(seg["text"])
            self.model.appendRow([text_id, speaker,  text, start, end])

        self.configure_column_widths()
