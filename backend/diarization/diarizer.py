import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import numpy as np
import torch

from config import DIARIZATION_MODEL, HF_TOKEN
from utils.gpu import register_model, unload_model
from utils.logger import get_logger

if TYPE_CHECKING:
    from pyannote.audio import Pipeline

logger = get_logger(__name__)

_pipeline: Optional["Pipeline"] = None


@dataclass
class SpeakerSegment:
    speaker: str
    start: float
    end: float


def load(hf_token: Optional[str] = None) -> None:
    """Load the pyannote speaker diarization pipeline."""
    global _pipeline
    token = hf_token or HF_TOKEN
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="torchcodec is not installed correctly")
        from pyannote.audio import Pipeline
    _pipeline = Pipeline.from_pretrained(DIARIZATION_MODEL, token=token)
    if torch.cuda.is_available():
        _pipeline = _pipeline.to(torch.device("cuda"))
    register_model("diarization", _pipeline)
    logger.info("pyannote diarization pipeline loaded")


def unload() -> None:
    global _pipeline
    _pipeline = None
    unload_model("diarization")


def diarize(audio: np.ndarray, sample_rate: int) -> list[SpeakerSegment]:
    """Return speaker-labeled time segments for the given audio."""
    if _pipeline is None:
        load()
    waveform = torch.from_numpy(audio).unsqueeze(0)  # (1, time)
    result = _pipeline({"waveform": waveform, "sample_rate": sample_rate})  # type: ignore[union-attr]
    annotation = result.speaker_diarization if hasattr(result, "speaker_diarization") else result
    return [
        SpeakerSegment(speaker=speaker, start=turn.start, end=turn.end)
        for turn, _, speaker in annotation.itertracks(yield_label=True)
    ]
