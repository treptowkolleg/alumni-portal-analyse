import os
import sys

import torch
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QIcon
from PyQt6.QtSvg import QSvgRenderer

from tools.lang import APP_TITLE

"""
Einstellungen
"""
WINDOW_TITLE = APP_TITLE
WINDOW_ICON = "favicon.ico"
WINDOW_RATIO = "16:9"
WINDOW_STYLE = "Fusion"

APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
<p>Diese Anwendung transkribiert Gespräche automatisch, erkennt einzelne Sprecher und erstellt strukturierte Gesprächsprotokolle – unterstützt durch moderne KI-Technologien.</p>
<p>Ideal für Interviews, Besprechungen oder Dokumentationen.</p>
"""

"""
Systemvariablen
"""
# Ordner
PROJECT_ROOT = os.path.dirname(os.path.abspath(sys.argv[0]))
AUDIO_PATH = os.path.join(PROJECT_ROOT, "audio")
IMAGE_PATH = os.path.join(PROJECT_ROOT, "assets/images")
ICON_PATH = os.path.join(PROJECT_ROOT, "assets/icons")

# Erzeuge Ordner, falls nicht vorhanden
os.makedirs(AUDIO_PATH, exist_ok=True)
os.makedirs(IMAGE_PATH, exist_ok=True)
os.makedirs(ICON_PATH, exist_ok=True)

WHISPER_MODEL_SIZE = "large"
WHISPER_SPEAKER_RULE = "liberal"

CPU_USAGE_UPDATE_RATE = 1000

# Mindestbreite der App
MIN_WIDTH = 1280

# Seitenverhältnisse
ratios_named = {
    "16:9": (16, 9),
    "4:3": (4, 3),
    "3:2": (3, 2),
    "1:1": (1, 1)
}

# CUDA-System
GPU_NAME = torch.cuda.get_device_name(0) if torch.backends.cudnn.enabled and torch.cuda.is_available() else "None"
CPU_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

"""
LL-Modelle
"""
MODELS = {
    "NeuralBeagle": "eas/neuralbeagle14",
    "Gemma": "gemma3n:e4b",
    "Gemma-2B": "gemma3n:e2b",
    "Gemma-2B-Instruct": "gemma:2b-instruct",
    "Open Hermes": "openhermes",
    "LLama": "llama3.1",
    "LLama:8B": "llama3:8b-instruct-q5_K_M",
    "Deepseek": "deepseek-r1:8b",
    "Qwen": "qwen3:8b",
    "Phi-Mini": "phi3:mini",
    "OpenLLM Deutsch": "jobautomation/OpenEuroLLM-German",
}

CURRENT_MODEL = MODELS["Gemma-2B"]


def get_min_size(ratio: str = "16:9"):
    """
    Maße der Fenstermaße ermitteln
    """
    min_sizes = {
        name: (MIN_WIDTH, int(MIN_WIDTH * h / w))
        for name, (w, h) in ratios_named.items()
    }
    return min_sizes.get(ratio, "16:9")


def get_rel_path(abs_path: str, file: str = None):
    """
    Relativen Pfad ermitteln
    """
    path = os.path.relpath(abs_path, PROJECT_ROOT)
    if file is not None:
        path = os.path.join(path, file)
    return path

def svg_to_icon(icon, size=24):
    """Konvertiert eine SVG-Datei in einen QIcon"""
    renderer = QSvgRenderer(get_rel_path(ICON_PATH, f"{icon}.svg"))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)  # Transparenter Hintergrund
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)
