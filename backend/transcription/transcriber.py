from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
from faster_whisper import WhisperModel

from config import WHISPER_COMPUTE_TYPE, WHISPER_MODEL
from utils.gpu import register_model, unload_model
from utils.logger import get_logger

logger = get_logger(__name__)

_model: Optional[WhisperModel] = None


@dataclass
class TranscriptChunk:
    text: str
    start: float
    end: float
    confidence: float


def load() -> None:
    """Load faster-whisper onto GPU (falls back to CPU if CUDA unavailable)."""
    global _model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        model_name = WHISPER_MODEL
        compute_type = WHISPER_COMPUTE_TYPE
    else:
        model_name = "base"
        compute_type = "int8"
        logger.warning("No CUDA GPU detected — using Whisper base (int8/CPU). Transcription will be slower.")
    _model = WhisperModel(model_name, device=device, compute_type=compute_type)
    register_model("whisper", _model)
    logger.info("faster-whisper %s loaded (device=%s, compute_type=%s)", model_name, device, compute_type)


def unload() -> None:
    global _model
    _model = None
    unload_model("whisper")


def transcribe(audio: np.ndarray) -> list[TranscriptChunk]:
    """Transcribe a float32 PCM array, returning timed text chunks."""
    if _model is None:
        load()
    segments, _ = _model.transcribe(audio, beam_size=5, task="translate")  # type: ignore[union-attr]
    return [
        TranscriptChunk(
            text=seg.text.strip(),
            start=seg.start,
            end=seg.end,
            confidence=float(seg.avg_logprob),
        )
        for seg in segments
        if seg.text.strip()
    ]
