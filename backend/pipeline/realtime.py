import asyncio
import uuid
from typing import Any, Callable, Coroutine

import numpy as np

import audio.capture as capture
from config import CHUNK_DURATION, SAMPLE_RATE
from diarization.diarizer import SpeakerSegment, diarize
from storage.models import Segment
from storage.queries import insert_segment
from transcription.transcriber import TranscriptChunk, transcribe
from vad.detector import is_speech
from utils.logger import get_logger

logger = get_logger(__name__)

BroadcastFn = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]

_buffer: list[np.ndarray] = []
_buffer_duration: float = 0.0


_speech_chunks_seen = 0


async def process_chunk(chunk: np.ndarray, meeting_id: str, broadcast: BroadcastFn) -> None:
    """Run VAD → STT → diarization on a chunk and stream results to the frontend."""
    global _buffer, _buffer_duration, _speech_chunks_seen

    if not is_speech(chunk):
        return

    _speech_chunks_seen += 1
    if _speech_chunks_seen % 10 == 1:
        logger.debug("VAD: speech chunk #%d, buffer=%.1fs", _speech_chunks_seen, _buffer_duration)

    _buffer.append(chunk)
    _buffer_duration += len(chunk) / SAMPLE_RATE

    if _buffer_duration < CHUNK_DURATION:
        return

    logger.info("Buffer full (%.1fs), running transcription", _buffer_duration)
    audio = np.concatenate(_buffer)
    _buffer = []
    _buffer_duration = 0.0

    loop = asyncio.get_event_loop()
    transcript_chunks: list[TranscriptChunk] = await loop.run_in_executor(None, transcribe, audio)
    speaker_segments: list[SpeakerSegment] = await loop.run_in_executor(None, diarize, audio, SAMPLE_RATE)

    logger.info("Transcription produced %d chunk(s)", len(transcript_chunks))
    for tc in transcript_chunks:
        speaker = _assign_speaker(tc.start, tc.end, speaker_segments)
        segment = Segment(
            id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            speaker=speaker,
            text=tc.text,
            start_time=tc.start,
            end_time=tc.end,
            confidence=tc.confidence,
        )
        await insert_segment(segment)
        await broadcast(
            {
                "speaker": segment.speaker,
                "text": segment.text,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "confidence": segment.confidence,
            }
        )


def _assign_speaker(start: float, end: float, segments: list[SpeakerSegment]) -> str:
    """Return the speaker with the greatest overlap with the [start, end] window."""
    best_speaker = "Unknown"
    best_overlap = 0.0
    for seg in segments:
        overlap = min(end, seg.end) - max(start, seg.start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = seg.speaker
    return best_speaker


async def flush_buffer(meeting_id: str, broadcast: BroadcastFn) -> None:
    """Process any remaining buffered audio that hasn't reached CHUNK_DURATION yet."""
    global _buffer, _buffer_duration
    if not _buffer:
        return
    audio = np.concatenate(_buffer)
    _buffer = []
    _buffer_duration = 0.0
    loop = asyncio.get_event_loop()
    transcript_chunks: list[TranscriptChunk] = await loop.run_in_executor(None, transcribe, audio)
    speaker_segments: list[SpeakerSegment] = await loop.run_in_executor(None, diarize, audio, SAMPLE_RATE)
    for tc in transcript_chunks:
        speaker = _assign_speaker(tc.start, tc.end, speaker_segments)
        segment = Segment(
            id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            speaker=speaker,
            text=tc.text,
            start_time=tc.start,
            end_time=tc.end,
            confidence=tc.confidence,
        )
        await insert_segment(segment)
        await broadcast(
            {
                "speaker": segment.speaker,
                "text": segment.text,
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "confidence": segment.confidence,
            }
        )


def reset_buffer() -> None:
    global _buffer, _buffer_duration
    _buffer = []
    _buffer_duration = 0.0
