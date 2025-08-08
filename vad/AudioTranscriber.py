import hdbscan
import numpy as np
import soundfile as sf
from PyQt6.QtCore import QObject, pyqtSignal
from ctranslate2 import Encoder
from faster_whisper import WhisperModel
from scipy.io.wavfile import write
from sklearn.preprocessing import normalize

from tools.desktop import CPU_DEVICE, WHISPER_MODEL_SIZE
from vad.VoiceActivityDetector import VAD_SAMPLING_RATE, read_audio
from resemblyzer import VoiceEncoder, preprocess_wav
from resemblyzer.hparams import sampling_rate

whisper = WhisperModel(WHISPER_MODEL_SIZE, compute_type="int8", device=CPU_DEVICE)


class AudioTranscriber:
    id_count = 0

    def __init__(self):
        self.encoder = VoiceEncoder()

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
        """Erstelle Speaker-Embeddings mit strengen Kriterien"""
        wav = preprocess_wav(wav)
        duration = len(wav) / sampling_rate

        # Für sehr kurze Aufnahmen - immer ein Sprecher
        if duration < 5:
            return [(0.0, duration, "Sprecher_0")]

        # Standard-Parameter für mittlere Aufnahmen
        window_size = 2.0
        hop_size = 1.0
        segments = []

        # Segmente erstellen
        for start in np.arange(0, duration - window_size + 0.1, hop_size):
            end = min(start + window_size, duration)
            segment = wav[int(start * sampling_rate):int(end * sampling_rate)]

            if len(segment) > sampling_rate * 0.5:
                try:
                    embed = self.encoder.embed_utterance(segment)
                    segments.append((start, end, embed))
                except:
                    continue

        # Wenn zu wenige Segmente, dann ein Sprecher
        if len(segments) < 3:
            return [(0.0, duration, "Sprecher_0")]

        # Embeddings analysieren
        embeddings = np.array([e for (_, _, e) in segments])

        # STRENGE Prüfung: Ähnlichkeit der Embeddings
        embeddings_normalized = normalize(embeddings, norm='l2')

        # Durchschnittliche paarweise Distanz berechnen
        distances = []
        for i in range(len(embeddings_normalized)):
            for j in range(i + 1, len(embeddings_normalized)):
                # Cosine-Distanz
                dist = np.dot(embeddings_normalized[i], embeddings_normalized[j])
                distances.append(dist)

        avg_similarity = np.mean(distances) if distances else 0

        # Wenn sehr hohe Ähnlichkeit, dann wahrscheinlich ein Sprecher
        if avg_similarity > 0.5:  # Sehr streng!
            print(f"Sehr hohe Ähnlichkeit ({avg_similarity:.3f}) - wahrscheinlich ein Sprecher")
            return [(0.0, duration, "Sprecher_0")]

        # Clustering mit STRENGEN Parametern
        clustering = hdbscan.HDBSCAN(
            min_cluster_size=max(3, len(segments) // 2),  # Sehr streng
            min_samples=2,
            cluster_selection_epsilon=0.5,  # Mindestabstand zwischen Clustern
            cluster_selection_method='eom',
            allow_single_cluster=True  # Lieber ein Cluster als viele kleine
        )
        labels = clustering.fit_predict(embeddings_normalized)

        # Analyse der Cluster-Qualität
        unique_labels = set(labels)
        normal_clusters = [l for l in unique_labels if l != -1]

        # Wenn nur ein oder kein echter Cluster, dann ein Sprecher
        if len(normal_clusters) <= 1:
            return [(0.0, duration, "Sprecher_0")]

        # Sehr ähnliche Cluster zusammenführen
        if len(normal_clusters) > 1:
            # Prüfe, ob Cluster wirklich unterschiedlich sind
            cluster_centers = {}
            for cluster_id in normal_clusters:
                cluster_embeddings = embeddings_normalized[labels == cluster_id]
                cluster_centers[cluster_id] = np.mean(cluster_embeddings, axis=0)

            # Ähnlichkeit zwischen Cluster-Zentren
            cluster_similarities = []
            cluster_ids = list(cluster_centers.keys())
            for i in range(len(cluster_ids)):
                for j in range(i + 1, len(cluster_ids)):
                    sim = np.dot(cluster_centers[cluster_ids[i]], cluster_centers[cluster_ids[j]])
                    cluster_similarities.append(sim)

            avg_cluster_similarity = np.mean(cluster_similarities) if cluster_similarities else 0

            # Wenn Cluster zu ähnlich, dann ein Sprecher
            if avg_cluster_similarity > 0.5:  # Sehr streng!
                print(f"Cluster zu ähnlich ({avg_cluster_similarity:.3f}) - ein Sprecher")
                return [(0.0, duration, "Sprecher_0")]

        # Nur wenn wirklich unterschiedliche Sprecher erkannt werden
        if len(normal_clusters) >= 2:
            # Speaker-Namen zuweisen
            label_to_name = {}
            for i, label in enumerate(sorted(normal_clusters)):
                label_to_name[label] = f"Sprecher_{i}"

            # Nur echte Sprecher-Segmente behalten
            speaker_segments = []
            for (start, end, _), label in zip(segments, labels):
                if label in label_to_name:  # Nur echte Cluster
                    speaker_segments.append((start, end, label_to_name[label]))

            if speaker_segments:
                # Zusammenführen und zurückgeben
                merged = self.merge_speaker_segments(speaker_segments)
                return merged[:2]  # Maximal 2 Sprecher für bessere Qualität

        # Fallback: Ein Sprecher
        return [(0.0, duration, "Sprecher_0")]

    def merge_speaker_segments(self, speaker_segments):
        """Konservativ zusammenführen"""
        if not speaker_segments:
            return []

        merged = [list(speaker_segments[0])]  # Erstes Segment

        for start, end, speaker in speaker_segments[1:]:
            last_seg = merged[-1]

            # Nur zusammenführen wenn sehr nah und gleicher Sprecher
            if (speaker == last_seg[2] and
                    start - last_seg[1] < 0.5):  # Sehr kleine Lücke
                last_seg[1] = end
            else:
                merged.append([start, end, speaker])

        return [tuple(seg) for seg in merged]

    def merge_speaker_with_transcript(self, transcript_segments, speaker_segments):
        """Führe Speaker-Informationen mit Transkript-Segmenten zusammen"""
        if not speaker_segments or not transcript_segments:
            for seg in transcript_segments:
                seg["speaker"] = "Sprecher_0"
            return transcript_segments

        # Für jedes Transkript-Segment den passenden Sprecher finden
        for transcript_seg in transcript_segments:
            segment_start = transcript_seg["start"]
            segment_end = transcript_seg["end"]

            speaker = self.find_speaker_for_segment(segment_start, segment_end, speaker_segments)
            transcript_seg["speaker"] = speaker

        return transcript_segments

    def find_speaker_for_segment(self, segment_start, segment_end, speaker_segments):
        """Finde den Sprecher - konservativ"""
        if not speaker_segments:
            return "Sprecher_0"

        # Einfache Überlappung - aber nur wenn klar
        best_speaker = "Sprecher_0"
        max_overlap = 0

        for speaker_start, speaker_end, speaker_name in speaker_segments:
            overlap_start = max(segment_start, speaker_start)
            overlap_end = min(segment_end, speaker_end)

            if overlap_start < overlap_end:
                overlap_duration = overlap_end - overlap_start
                if overlap_duration > max_overlap:
                    max_overlap = overlap_duration
                    best_speaker = speaker_name

        return best_speaker