from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QStandardItem, QColor, QBrush
from PyQt6.QtWidgets import QHeaderView, QAbstractItemView

from gui.SpeakerDelegate import SpeakerDelegate
from gui.TableView import TableView


class TranscriptTable(TableView):
    speakerChanged = pyqtSignal(int, str)

    def __init__(self, data_manager, parent=None):
        super(TranscriptTable, self).__init__(["ID", "Nr.", "Sprecher", "Text", "Start", "Ende"], parent)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.data_manager = data_manager
        self.configure_column_widths()
        self.speaker_colors = {}
        self.setItemDelegateForColumn(2, SpeakerDelegate(self))
        self.model.itemChanged.connect(self.on_item_changed)

        self.setColumnHidden(1, True)
        self.setAutoScroll(True)

        #self.setGridStyle(Qt.PenStyle.SolidLine)

        self.setStyleSheet("""
                    QTableView::item:selected {
                        background-color: rgba(255, 255, 255, 15%);
                    }
                """)

    def format_time(self, seconds):
        """Formatiere Sekunden in HH:MM:SS.ms oder MM:SS.ms"""
        try:
            seconds_float = float(seconds)
            hours = int(seconds_float // 3600)
            minutes = int((seconds_float % 3600) // 60)
            secs = int(seconds_float % 60)

            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        except (ValueError, TypeError):
            return str(seconds)

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
                    self.update_colors()
                except ValueError:
                    pass  # Ungültige ID

    def update_speaker_for_ids(self, ids, new_speaker):
        """Aktualisiert den Sprecher für mehrere IDs"""
        for row in range(self.model.rowCount()):
            id_item = self.model.item(row, 0)  # Spalte "Nr" (idn)
            speaker_item = self.model.item(row, 2)  # Spalte "Sprecher"

            if id_item and speaker_item:
                try:
                    idn = int(id_item.text())
                    if idn in ids:
                        speaker_item.setText(new_speaker)
                except ValueError:
                    pass

        self.update_colors()

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

    def remove_all_rows(self):
        self.model.removeRows(0, self.model.rowCount())

    def remove_row(self, row):
        self.model.removeRow(row)

    def update_transcript_table(self, segments):

        self.speaker_colors = self.generate_speaker_colors(segments)

        for seg in segments:

            id = QStandardItem(str(seg["idn"]))
            text_id = QStandardItem(str(seg["id"]))
            speaker = QStandardItem(str(seg["speaker"]))
            start = QStandardItem(self.format_time(seg["start"]))
            end = QStandardItem(self.format_time(seg["end"]))
            text = QStandardItem(seg["text"])

            start.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            end.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            for item in [id, text_id, text, start, end]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            self.model.appendRow([id, text_id, speaker, text, start, end])

        self.configure_column_widths()
        self.update_colors()
        self.scrollToBottom()

    def update_colors(self):
        """Aktualisiere alle Farben basierend auf aktuellen Sprechern"""
        # Sammle alle aktuellen Sprecher
        current_speakers = set()
        for row in range(self.model.rowCount()):
            speaker_item = self.model.item(row, 2)  # Spalte "Sprecher"
            if speaker_item:
                current_speakers.add(speaker_item.text())

        # Generiere neue Farben
        segments_for_color_gen = []
        for row in range(self.model.rowCount()):
            speaker_item = self.model.item(row, 2)
            if speaker_item:
                segments_for_color_gen.append({"speaker": speaker_item.text()})

        self.speaker_colors = self.generate_speaker_colors(segments_for_color_gen)

        # Wende neue Farben an
        for row in range(self.model.rowCount()):
            speaker_item = self.model.item(row, 2)
            if speaker_item:
                speaker_name = speaker_item.text()
                items = [
                    self.model.item(row, 0),  # Nr
                    self.model.item(row, 1),  # ID
                    speaker_item,  # Sprecher
                    self.model.item(row, 3),  # Text
                    self.model.item(row, 4),  # Start
                    self.model.item(row, 5),  # Ende
                ]
                self.apply_row_colors(items, speaker_name)

    def apply_row_colors(self, items, speaker_name):
        """Wende Farben auf eine Zeile an"""
        color = self.speaker_colors.get(speaker_name, QColor(255, 255, 255))
        brush = QBrush(color)
        for item in items:
            if item:  # Sicherstellen, dass Item existiert
                item.setBackground(brush)

    def generate_speaker_colors(self, segments):
        """Generiere eindeutige Farben für jeden Sprecher"""
        speakers = list(set(str(seg["speaker"]) for seg in segments))
        colors = {}

        # Definiere eine Liste von schönen Farben
        color_palette = [
            QColor(52, 199, 89, 90),
            QColor(88, 86, 214, 90),
            QColor(255, 149, 0, 90),
            QColor(255, 45, 85, 90),
            QColor(175, 82, 222, 90),
            QColor(255, 59, 48, 90),
            QColor(90, 200, 250, 90),
        ]

        for i, speaker in enumerate(speakers):
            if i < len(color_palette):
                colors[speaker] = color_palette[i]
            else:
                import hashlib
                hash_val = int(hashlib.md5(speaker.encode()).hexdigest()[:8], 16)
                # Dunklere Farben durch niedrigere Werte
                r = (hash_val & 0xFF0000) >> 16
                g = (hash_val & 0x00FF00) >> 8
                b = hash_val & 0x0000FF
                # Mache Farben dunkler
                r = max(20, r // 2)
                g = max(20, g // 2)
                b = max(20, b // 2)
                colors[speaker] = QColor(r, g, b)

        return colors
