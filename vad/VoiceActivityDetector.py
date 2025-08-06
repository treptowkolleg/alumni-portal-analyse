from collections import deque

import numpy as np
from sympy.printing.pytorch import torch

VAD_SAMPLING_RATE = 16000
VAD_BLOCK_SIZE = 512
VAD_CHANNELS = 1
VAD_POST_SPEECH_SECONDS = 5
VAD_SPEECH_PADDING = .5

# VAD-Thresholds
PRE_SPEECH_PADDING = int(VAD_SPEECH_PADDING * VAD_SAMPLING_RATE)
POST_SPEECH_PADDING = int(VAD_SPEECH_PADDING * VAD_SAMPLING_RATE)
MAX_SILENCE_SAMPLES = VAD_POST_SPEECH_SECONDS * VAD_SAMPLING_RATE
PRE_BUFFER = deque(maxlen=PRE_SPEECH_PADDING)

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad')
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils


class VoiceActivityDetector:

    def __init__(self):
        """
        Klasse konstruieren und Attribute bereitstellen
        """

        self.recording = []
        self.is_recording = False
        self.post_speech_countdown = 0
        self.silence_samples = 0

    def simple_vad(self, audio_np):
        audio_tensor = torch.from_numpy(audio_np).float().unsqueeze(0)
        return model(audio_tensor, VAD_SAMPLING_RATE).item()

    def audio_callback(self, indata, frames, time, status):
        audio = indata[:, 0]
        PRE_BUFFER.extend(audio)

        speech_prob = self.simple_vad(audio)

        if speech_prob > 0.6:
            if not self.is_recording:
                print("🔴 \tSprache erkannt")
                self.silence_samples = 0
                self.recording.append(np.array(PRE_BUFFER))
            self.is_recording = True
            self.post_speech_countdown = POST_SPEECH_PADDING
            self.recording.append(audio.copy())
        else:
            if self.is_recording:
                if self.post_speech_countdown > 0:
                    self.recording.append(audio.copy())
                    self.post_speech_countdown -= len(audio)
                else:
                    print("⏸️ \tAufnahme pausiert")
                    self.is_recording = False
            self.silence_samples += len(audio)
