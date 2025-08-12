from PyQt6.QtGui import QStandardItem
from PyQt6.QtWidgets import QHeaderView, QComboBox, QAbstractItemView
from PyQt6.QtCore import Qt

from gui.TableView import TableView


class SpeakerTable(TableView):
    def __init__(self, data_manager, parent=None):
        super(SpeakerTable, self).__init__(["Transkript-IDs", "Sprecher"], parent)
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.data_manager = data_manager
        self.configure_column_widths()
        self.id_combos = {}  # Speichere Referenzen zu ComboBoxen
        self.segments_cache = []


    def update_speaker_for_id(self, idn, new_speaker):
        """Aktualisiert den Sprecher für eine bestimmte ID direkt"""
        # Finde das Segment mit der ID und ändere den Sprecher
        for seg in self.segments_cache:
            if seg["idn"] == idn:
                seg["speaker"] = new_speaker
                break

        # Tabelle neu aufbauen mit aktualisierten Daten
        self.model.removeRows(0, self.model.rowCount())
        self.id_combos.clear()
        self.update_table(self.segments_cache)

    def configure_column_widths(self):
        header = self.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.resizeColumnsToContents()

        if self.columnWidth(0) < 100:
            self.setColumnWidth(0, 100)

    def merge_segments(self, new_segments):
        """Merge neue Segmente mit bestehendem Cache: neue ersetzen alte mit gleicher ID"""
        if not self.segments_cache and not new_segments:
            return []

        if not self.segments_cache:
            return new_segments.copy()

        if not new_segments:
            return self.segments_cache.copy()

        # Erstelle Dictionary aus bestehendem Cache
        cache_dict = {seg["idn"]: seg for seg in self.segments_cache}

        # Füge neue Segmente hinzu (ersetzen bestehende mit gleicher ID)
        for seg in new_segments:
            cache_dict[seg["idn"]] = seg

        # Konvertiere zurück zu Liste
        return list(cache_dict.values())

    def update_table(self, segments):

        self.segments_cache = self.merge_segments(segments)

        # Gruppiere Segmente nach Sprecher
        speaker_segments = {}
        for seg in self.segments_cache:
            speaker = seg["speaker"]
            if speaker not in speaker_segments:
                speaker_segments[speaker] = []
            speaker_segments[speaker].append(seg)

        # Füge zusammengefasste Einträge hinzu
        for speaker, segs in speaker_segments.items():
            # Alle IDs dieses Sprechers sammeln
            ids_list = [str(seg["idn"]) for seg in segs]

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