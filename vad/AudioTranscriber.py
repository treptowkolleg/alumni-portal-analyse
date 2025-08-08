import hdbscan
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel
from resemblyzer import VoiceEncoder, preprocess_wav
from resemblyzer.hparams import sampling_rate
from scipy.io.wavfile import write
from sklearn.preprocessing import normalize

from tools.desktop import CPU_DEVICE, WHISPER_MODEL_SIZE
from vad.VoiceActivityDetector import VAD_SAMPLING_RATE, read_audio

whisper = WhisperModel(WHISPER_MODEL_SIZE, compute_type="int8", device=CPU_DEVICE)


class AudioTranscriber:
    id_count = 0

    def __init__(self,
                 # Segmentierung
                 window_size=0.5,  # Sehr kurze Fenster für bessere Auflösung
                 hop_size=0.1,  # Stark überlappende Segmente
                 min_segments=3,

                 # Ähnlichkeitsschwellen
                 embedding_similarity_threshold=0.70,  # Weniger streng
                 cluster_similarity_threshold=0.55,  # Weniger streng

                 # Clustering-Parameter
                 min_cluster_size_factor=4,  # Weniger streng
                 min_samples=1,
                 cluster_selection_epsilon=0.15,  # Weniger streng
                 allow_single_cluster=False,

                 # Ergebnis-Parameter
                 max_speakers=5,
                 min_segment_duration=0.2,
                 merge_gap_threshold=0.3,

                 # Zeitbeschränkungen
                 min_duration_for_diarization=3):
        """
        AudioTranscriber mit optimierten Parametern für bessere Sprechererkennung
        """
        self.merge_gap_threshold = merge_gap_threshold
        self.allow_single_cluster = allow_single_cluster
        self.cluster_selection_epsilon = cluster_selection_epsilon
        self.min_samples = min_samples
        self.min_cluster_size_factor = min_cluster_size_factor
        self.min_segments = min_segments
        self.min_segment_duration = min_segment_duration
        self.hop_size = hop_size
        self.window_size = window_size
        self.min_duration_for_diarization = min_duration_for_diarization
        self.encoder = VoiceEncoder()

        # Alle Parameter speichern
        for key, value in locals().items():
            if key != 'self':
                setattr(self, key, value)

    def process_recording(self, recording):
        audio_data = np.concatenate(recording)
        write("output.wav", VAD_SAMPLING_RATE, (audio_data * 32767).astype(np.int16))

        wav = read_audio("output.wav", sampling_rate=VAD_SAMPLING_RATE)
        audio_data, sr = sf.read("output.wav")

        segments, _ = whisper.transcribe(audio_data, language="de", word_timestamps=True)

        whisper_segments = list(segments)
        result = []
        if not whisper_segments:
            pass
        else:
            for seg_idx, seg in enumerate(whisper_segments):
                result.append({
                    "id": self.id_count,
                    "start": round(seg.start, 1),
                    "end": round(seg.end, 1),
                    "text": seg.text.strip()
                })
                self.id_count += 1

        # Speaker Diarization durchführen
        speaker_segments = self.create_embeddings(audio_data)

        # Speaker-Informationen mit Whisper-Segmenten zusammenführen
        final_result = self.merge_speaker_with_transcript(result, speaker_segments)

        return final_result

    def create_embeddings(self, wav, min_segment_length=1.0):
        """Erstelle Speaker-Embeddings mit Distance Matrix und aggressiver Erkennung"""
        wav = preprocess_wav(wav)
        duration = len(wav) / sampling_rate

        print(f"DEBUG: Aufnahme: {duration:.2f}s")

        # Sehr früh beginnen mit Diarization
        if duration < self.min_duration_for_diarization:
            print(f"DEBUG: Zu kurz für Diarization ({duration}s < {self.min_duration_for_diarization}s)")
            return [(0.0, duration, "Sprecher 0")]

        segments = []

        # SEHR viele kurze Segmente erstellen
        positions = []
        current = 0
        while current < duration - self.window_size:
            positions.append(current)
            current += self.hop_size

        # Auch das Ende sicherstellen
        if positions and positions[-1] < duration - self.window_size:
            positions.append(duration - self.window_size)
        elif not positions:
            positions.append(0)

        print(f"DEBUG: Erstelle {len(positions)} Segmente")

        for start in positions:
            end = min(start + self.window_size, duration)
            segment = wav[int(start * sampling_rate):int(end * sampling_rate)]

            if len(segment) > sampling_rate * self.min_segment_duration:
                try:
                    embed = self.encoder.embed_utterance(segment)
                    segments.append((start, end, embed))
                    # print(f"DEBUG: Segment {start:.1f}-{end:.1f}s erstellt")
                except Exception as e:
                    print(f"DEBUG: Fehler bei Segment {start:.1f}s: {e}")
                    continue

        if len(segments) < self.min_segments:
            print(f"DEBUG: Zu wenige Segmente ({len(segments)} < {self.min_segments})")
            return [(0.0, duration, "Sprecher 0")]

        print(f"DEBUG: {len(segments)} Embeddings erstellt")

        # Embeddings analysieren - SEHR locker
        embeddings = np.array([e for (_, _, e) in segments])
        embeddings_normalized = normalize(embeddings, norm='l2').astype(np.float64)

        # **Manuelle Cosine-Distance Matrix** (kompatibel mit allen Versionen)
        n = len(embeddings_normalized)
        distance_matrix = np.zeros((n, n), dtype=np.float64)

        for i in range(n):
            for j in range(i, n):
                if i == j:
                    distance_matrix[i, j] = 0.0
                else:
                    # Cosine Distance = 1 - Cosine Similarity
                    cos_sim = np.dot(embeddings_normalized[i], embeddings_normalized[j])
                    cos_dist = 1.0 - cos_sim
                    distance_matrix[i, j] = cos_dist
                    distance_matrix[j, i] = cos_dist

        # Statistiken der Distance Matrix
        avg_distance = np.mean(distance_matrix)
        std_distance = np.std(distance_matrix)
        print(f"DEBUG: Distance Matrix - Mean: {avg_distance:.3f}, Std: {std_distance:.3f}")

        # **Aggressives Clustering mit Distance Matrix**
        clustering = hdbscan.HDBSCAN(
            min_cluster_size=max(2, len(segments) // self.min_cluster_size_factor),
            min_samples=self.min_samples,
            cluster_selection_epsilon=self.cluster_selection_epsilon,
            cluster_selection_method='leaf',  # Aggressiver
            metric='precomputed',  # Jetzt sicher!
            allow_single_cluster=self.allow_single_cluster,
            alpha=1.0
        )

        try:
            labels = clustering.fit_predict(distance_matrix)
            print(f"DEBUG: Clustering mit Distance Matrix abgeschlossen")
        except Exception as e:
            print(f"DEBUG: Clustering mit Distance Matrix fehlgeschlagen: {e}")
            # Fallback ohne Distance Matrix
            clustering = hdbscan.HDBSCAN(
                min_cluster_size=max(2, len(segments) // self.min_cluster_size_factor),
                min_samples=self.min_samples,
                cluster_selection_epsilon=self.cluster_selection_epsilon,
                cluster_selection_method='leaf',
                metric='euclidean',  # Fallback
                allow_single_cluster=False
            )
            labels = clustering.fit_predict(embeddings_normalized)

        # Analyse der Ergebnisse
        unique_labels = set(labels)
        normal_clusters = [l for l in unique_labels if l != -1]
        noise_count = list(labels).count(-1)

        print(f"DEBUG: Ergebnis - Cluster: {len(normal_clusters)}, Rauschen: {noise_count}")

        # **Erzwinge Sprechererkennung bei guten Bedingungen**
        if len(normal_clusters) <= 1:
            # Prüfe, ob genug Variation vorhanden ist
            if len(segments) >= 6 and avg_distance > 0.3:  # Ausreichende Distanz
                print("DEBUG: Ausreichende Variation - erzwinge Sprechererkennung")
                return self.force_speaker_detection(segments, duration, distance_matrix)

        # **Normale Verarbeitung wenn ausreichend Cluster**
        if len(normal_clusters) >= 2:
            return self.create_improved_speaker_timeline(segments, labels, normal_clusters, duration)

        return [(0.0, duration, "Sprecher 0")]

    def force_speaker_detection(self, segments, duration, distance_matrix):
        """Erzwinge Sprechererkennung basierend auf Distance Matrix"""
        n_segments = len(segments)

        # Einfache Aufteilung basierend auf maximale Distanz
        max_dist_indices = np.unravel_index(np.argmax(distance_matrix), distance_matrix.shape)
        seg1_idx, seg2_idx = max_dist_indices

        print(f"DEBUG: Maximaldistanz zwischen Segment {seg1_idx} und {seg2_idx}")

        # Zeitbasierte Aufteilung um die gefundenen Segmente
        mid_time = (segments[seg1_idx][0] + segments[seg1_idx][1] +
                    segments[seg2_idx][0] + segments[seg2_idx][1]) / 4

        return [
            (0.0, mid_time, "Sprecher 0"),
            (mid_time, duration, "Sprecher 1")
        ]

    def create_improved_speaker_timeline(self, segments, labels, normal_clusters, duration):
        """Erstelle verbesserte Sprecher-Zeitleiste ohne Überlappungen"""
        # Speaker-Namen zuweisen
        label_to_name = {}
        for i, label in enumerate(sorted(normal_clusters)):
            label_to_name[label] = f"Sprecher {i}"

        # Erstelle Zeitlinie mit allen Segmenten
        time_speaker_map = {}

        # Für jedes Zeitintervall sammle alle Sprecher-Votes
        time_resolution = 0.1  # Sekunden (feinere Auflösung)
        max_time = duration

        for t in np.arange(0, max_time, time_resolution):
            votes = {}
            for (start, end, _), label in zip(segments, labels):
                if start <= t < end and label in normal_clusters:
                    speaker_name = label_to_name[label]
                    if speaker_name not in votes:
                        votes[speaker_name] = 0
                    votes[speaker_name] += 1

            if votes:
                # Wähle Sprecher mit meisten Votes
                dominant_speaker = max(votes, key=votes.get)
                time_speaker_map[t] = dominant_speaker

        # Konvertiere Zeitlinie zu Segmenten
        if not time_speaker_map:
            return [(0.0, duration, "Sprecher 0")]

        # Gruppiere aufeinanderfolgende gleiche Sprecher
        times = sorted(time_speaker_map.keys())
        speaker_segments = []

        if times:
            current_speaker = time_speaker_map[times[0]]
            segment_start = times[0]

            for t in times[1:]:
                speaker = time_speaker_map[t]
                if speaker != current_speaker:
                    # Neuer Sprecher
                    speaker_segments.append((segment_start, t, current_speaker))
                    current_speaker = speaker
                    segment_start = t

            # Letztes Segment
            speaker_segments.append((segment_start, times[-1] + time_resolution, current_speaker))

        # Final cleanup: Entferne sehr kurze Segmente
        cleaned_segments = []
        for start, end, speaker in speaker_segments:
            if end - start >= 1.0:  # Mindestlänge 1 Sekunde
                cleaned_segments.append((start, end, speaker))

        if cleaned_segments:
            print(f"DEBUG: Verbesserte Ergebnisse: {len(cleaned_segments)} Sprecher")
            for seg in cleaned_segments:
                print(f"  {seg[2]}: {seg[0]:.1f}-{seg[1]:.1f}s")
            return cleaned_segments

        return [(0.0, duration, "Sprecher 0")]

    def merge_speaker_segments(self, speaker_segments):
        """Konservativ zusammenführen mit konfigurierbarem Schwellwert"""
        if not speaker_segments:
            return []

        merged = [list(speaker_segments[0])]  # Erstes Segment

        for start, end, speaker in speaker_segments[1:]:
            last_seg = merged[-1]

            # Nur zusammenführen wenn sehr nah und gleicher Sprecher
            if (speaker == last_seg[2] and
                    start - last_seg[1] < self.merge_gap_threshold):
                last_seg[1] = end
            else:
                merged.append([start, end, speaker])

        return [tuple(seg) for seg in merged]

    def merge_speaker_with_transcript(self, transcript_segments, speaker_segments):
        """Führe Speaker-Informationen mit Transkript-Segmenten zusammen"""
        if not speaker_segments or not transcript_segments:
            for seg in transcript_segments:
                seg["speaker"] = "Sprecher 0"
            return transcript_segments

        # Für jedes Transkript-Segment den passenden Sprecher finden
        for transcript_seg in transcript_segments:
            segment_start = transcript_seg["start"]
            segment_end = transcript_seg["end"]

            speaker = self.find_speaker_for_segment(segment_start, segment_end, speaker_segments)
            transcript_seg["speaker"] = speaker

        return transcript_segments

    def find_speaker_for_segment(self, segment_start, segment_end, speaker_segments):
        """Finde den Sprecher - verbesserte Methode"""
        if not speaker_segments:
            return "Sprecher 0"

        # Berechne Überlappung mit allen Sprecher-Segmenten
        best_speaker = "Sprecher 0"
        max_overlap = 0

        for speaker_start, speaker_end, speaker_name in speaker_segments:
            overlap_start = max(segment_start, speaker_start)
            overlap_end = min(segment_end, speaker_end)

            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    best_speaker = speaker_name

        # Wenn keine Überlappung, nehme zeitlich nächsten Sprecher
        if max_overlap == 0:
            min_distance = float('inf')
            for speaker_start, speaker_end, speaker_name in speaker_segments:
                segment_mid = (segment_start + segment_end) / 2
                speaker_mid = (speaker_start + speaker_end) / 2
                distance = abs(segment_mid - speaker_mid)
                if distance < min_distance:
                    min_distance = distance
                    best_speaker = speaker_name

        return best_speaker

    def set_preset(self, preset_name):
        """Setze vordefinierte Parameter-Sets"""
        presets = {
            'conservative': {  # Sehr konservativ
                'window_size': 2.0,
                'hop_size': 1.0,
                'min_segments': 5,
                'embedding_similarity_threshold': 0.95,
                'cluster_similarity_threshold': 0.85,
                'min_cluster_size_factor': 2,
                'max_speakers': 2
            },
            'balanced': {  # Ausgewogen
                'window_size': 1.5,
                'hop_size': 0.5,
                'min_segments': 4,
                'embedding_similarity_threshold': 0.90,
                'cluster_similarity_threshold': 0.75,
                'min_cluster_size_factor': 3,
                'max_speakers': 3
            },
            'liberal': {  # Locker - beste Sprechererkennung
                'window_size': 0.5,
                'hop_size': 0.1,
                'min_segments': 3,
                'embedding_similarity_threshold': 0.70,
                'cluster_similarity_threshold': 0.55,
                'min_cluster_size_factor': 4,
                'max_speakers': 5,
                'min_duration_for_diarization': 3
            }
        }

        if preset_name in presets:
            preset = presets[preset_name]
            for key, value in preset.items():
                if hasattr(self, key):
                    setattr(self, key, value)
