import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"
MODELS_DIR = BASE_DIR / "models"
DB_PATH = DATA_DIR / "recap.db"

# Audio params
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 5  # seconds for Whisper windows

HF_TOKEN: str | None = os.environ.get("HF_TOKEN")

# Model names
WHISPER_MODEL = "large-v3"
WHISPER_COMPUTE_TYPE = "float16"
DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"
OLLAMA_MODEL = "mistral"
OLLAMA_BASE_URL = "http://localhost:11434"

# Server
HOST = "0.0.0.0"
PORT = 8420
