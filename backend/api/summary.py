from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from pipeline.post_meeting import run as run_post_meeting
from storage.queries import get_meeting
from utils.logger import get_logger

router = APIRouter(prefix="/meetings", tags=["summary"])
logger = get_logger(__name__)


class SummaryOut(BaseModel):
    meeting_id: str
    overview: str
    key_points: list[str]
    action_items: list[str]
    generated_at: str


@router.post("/{meeting_id}/summarize", response_model=SummaryOut)
async def trigger_summarize(meeting_id: str):
    if not await get_meeting(meeting_id):
        raise HTTPException(status_code=404, detail="Meeting not found")
    summary = await run_post_meeting(meeting_id)
    return SummaryOut(**summary.__dict__)
