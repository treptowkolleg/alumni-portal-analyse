from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QHeaderView, QComboBox
from PyQt6.QtCore import Qt

from gui.TableView import TableView


class SpeakerTable(TableView):
    def __init__(self, parent=None):
        super(SpeakerTable, self).__init__(["Transkript-IDs", "Sprecher"], parent)
        self.configure_column_widths()
        self.id_combos = {}  # Speichere Referenzen zu ComboBoxen

    def configure_column_widths(self):
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.resizeColumnsToContents()

        if self.columnWidth(0) < 100:
            self.setColumnWidth(0, 100)

    def update_table(self, segments):
        # Zuerst leeren wir die Tabelle
        self.model.removeRows(0, self.model.rowCount())
        self.id_combos.clear()

        # Gruppiere Segmente nach Sprecher
        speaker_segments = {}
        for seg in segments:
            speaker = seg["speaker"]
            if speaker not in speaker_segments:
                speaker_segments[speaker] = []
            speaker_segments[speaker].append(seg)

        # Füge zusammengefasste Einträge hinzu
        for speaker, segs in speaker_segments.items():
            # Alle IDs dieses Sprechers sammeln
            ids_list = [str(seg["id"]) for seg in segs]

            # Erstelle Model-Items
            ids_display = QStandardItem(", ".join(ids_list))  # Anzeige aller IDs
            speaker_id = QStandardItem(str(speaker))

            # Füge Zeile hinzu
            row = self.model.rowCount()
            self.model.appendRow([ids_display, speaker_id])

            # Erstelle und setze ComboBox
            combo = QComboBox()
            combo.addItems(ids_list)
            if ids_list:
                combo.setCurrentText(ids_list[0])  # Erste ID als Standard

            self.setIndexWidget(self.model.index(row, 0), combo)

            # Speichere Referenz für späteren Zugriff
            self.id_combos[speaker] = combo

        self.configure_column_widths()

    def get_selected_id_for_speaker(self, speaker):
        """Gibt die aktuell ausgewählte ID für einen Sprecher zurück"""
        if speaker in self.id_combos:
            return self.id_combos[speaker].currentText()
        return None