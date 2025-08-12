from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QHeaderView, QAbstractItemView

from gui.SpeakerDelegate import SpeakerDelegate
from gui.TableView import TableView


class TranscriptTable(TableView):
    speakerChanged = pyqtSignal(int, str)

    def __init__(self, data_manager, parent=None):
        super(TranscriptTable, self).__init__(["Nr", "ID", "Sprecher", "Text", "Start", "Ende"], parent)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.data_manager = data_manager
        self.configure_column_widths()

        self.setItemDelegateForColumn(2, SpeakerDelegate(self))
        self.model.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        # Prüfe, ob sich der Sprecher geändert hat
        col = item.column()
        row = item.row()
        if col == 2:  # Spalte "Sprecher"
            id_item = self.model.item(row, 0)
            if id_item:
                try:
                    idn = int(id_item.text())
                    new_speaker = item.text()
                    self.speakerChanged.emit(idn, new_speaker)
                except ValueError:
                    pass  # Ungültige ID

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
