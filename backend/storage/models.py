from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Meeting:
    id: str
    title: str
    started_at: str
    ended_at: Optional[str] = None
    status: str = "recording"  # recording | processing | completed
    audio_path: Optional[str] = None


@dataclass
class Segment:
    id: str
    meeting_id: str
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float] = None
    created_at: str = ""


@dataclass
class Summary:
    meeting_id: str
    overview: str
    key_points: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)
    generated_at: str = ""
