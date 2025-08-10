from PyQt6.QtCore import QObject, pyqtSignal


class TranscriptDataManager(QObject):
    """Zentrales Datenmanagement für beide Tabellen"""
    dataUpdated = pyqtSignal()  # Signal für UI-Updates

    def __init__(self):
        super().__init__()
        self.segments = []

    def update_segments(self, segments):
        """Neue Segmente setzen"""
        self.segments = segments
        self.dataUpdated.emit()

    def update_segment_speaker(self, segment_id, new_speaker):
        """Sprecher für spezifische Segment-ID ändern"""
        changed = False
        for seg in self.segments:
            if seg["idn"] == segment_id:  # idn als Zuordnungspunkt
                seg["speaker"] = new_speaker
                changed = True

        if changed:
            self.dataUpdated.emit()  # Beide Tabellen aktualisieren

    def get_segments(self):
        return self.segments.copy()

    def get_segment_by_id(self, segment_id):
        """Einzelnes Segment per ID finden"""
        for seg in self.segments:
            if seg["idn"] == segment_id:
                return seg
        return None