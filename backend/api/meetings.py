from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from storage.queries import delete_meeting, get_meeting, get_segments, get_summary, list_meetings
from utils.logger import get_logger

router = APIRouter(prefix="/meetings", tags=["meetings"])
logger = get_logger(__name__)


class SegmentOut(BaseModel):
    id: str
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: float | None


class SummaryOut(BaseModel):
    overview: str
    key_points: list[str]
    action_items: list[str]
    generated_at: str


class MeetingOut(BaseModel):
    id: str
    title: str
    started_at: str
    ended_at: str | None
    status: str


class MeetingDetailOut(MeetingOut):
    segments: list[SegmentOut]
    summary: SummaryOut | None


@router.get("/", response_model=list[MeetingOut])
async def get_meetings():
    return await list_meetings()


@router.get("/{meeting_id}", response_model=MeetingDetailOut)
async def get_meeting_detail(meeting_id: str):
    meeting = await get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    segments = await get_segments(meeting_id)
    summary = await get_summary(meeting_id)
    return MeetingDetailOut(
        **meeting.__dict__,
        segments=[SegmentOut(**s.__dict__) for s in segments],
        summary=SummaryOut(**summary.__dict__) if summary else None,
    )


@router.delete("/{meeting_id}")
async def remove_meeting(meeting_id: str):
    if not await get_meeting(meeting_id):
        raise HTTPException(status_code=404, detail="Meeting not found")
    await delete_meeting(meeting_id)
    return {"status": "deleted"}
