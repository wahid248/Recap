from typing import Optional

import numpy as np
import torch

from config import SAMPLE_RATE
from utils.gpu import register_model, unload_model
from utils.logger import get_logger

logger = get_logger(__name__)

_model: Optional[object] = None


def load() -> None:
    """Download (if needed) and load the Silero VAD model via torch.hub."""
    global _model
    model, _ = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        verbose=False,
    )
    _model = model
    register_model("silero_vad", _model)
    logger.info("Silero VAD loaded")


def unload() -> None:
    global _model
    _model = None
    unload_model("silero_vad")


_VAD_SAMPLES = 512


def is_speech(chunk: np.ndarray, threshold: float = 0.5) -> bool:
    """Return True if any 512-sample window in the chunk contains speech."""
    if _model is None:
        load()
    if len(chunk) < _VAD_SAMPLES:
        chunk = np.pad(chunk, (0, _VAD_SAMPLES - len(chunk)))
    for i in range(0, len(chunk) - _VAD_SAMPLES + 1, _VAD_SAMPLES):
        window = chunk[i : i + _VAD_SAMPLES]
        tensor = torch.from_numpy(window).float()
        with torch.no_grad():
            confidence: float = _model(tensor, SAMPLE_RATE).item()  # type: ignore[union-attr]
        if confidence >= threshold:
            return True
    return False
