import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

import audio.capture as capture
from api.ws import broadcast
from pipeline.post_meeting import run as run_post_meeting
from pipeline.realtime import flush_buffer, process_chunk, reset_buffer
from storage.models import Meeting
from storage.queries import get_meeting, insert_meeting
from utils.logger import get_logger

router = APIRouter(prefix="/capture", tags=["capture"])
logger = get_logger(__name__)

_active_meeting_id: Optional[str] = None
_capture_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]


class StartResponse(BaseModel):
    meeting_id: str
    started_at: str


class StatusResponse(BaseModel):
    is_recording: bool
    meeting_id: Optional[str]
    started_at: Optional[str]


async def _capture_loop(meeting_id: str) -> None:
    """Continuously pull audio chunks and feed them through the realtime pipeline."""
    while True:
        chunk = capture.get_chunk()
        if chunk is not None and len(chunk) > 0:
            try:
                await process_chunk(chunk, meeting_id, broadcast)
            except Exception:
                logger.exception("Error processing audio chunk for meeting %s", meeting_id)
        await asyncio.sleep(0.01)


@router.get("/status", response_model=StatusResponse)
async def get_capture_status():
    if _active_meeting_id is None:
        return StatusResponse(is_recording=False, meeting_id=None, started_at=None)
    meeting = await get_meeting(_active_meeting_id)
    return StatusResponse(
        is_recording=True,
        meeting_id=_active_meeting_id,
        started_at=meeting.started_at if meeting else None,
    )


@router.post("/start", response_model=StartResponse)
async def start_capture():
    global _active_meeting_id, _capture_task
    if _active_meeting_id is not None:
        raise HTTPException(status_code=409, detail="Recording already in progress")

    meeting_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    await insert_meeting(
        Meeting(
            id=meeting_id,
            title=f"Meeting {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            started_at=started_at,
        )
    )
    capture.start()
    reset_buffer()
    _active_meeting_id = meeting_id
    _capture_task = asyncio.create_task(_capture_loop(meeting_id))
    logger.info("Capture started for meeting %s", meeting_id)
    return StartResponse(meeting_id=meeting_id, started_at=started_at)


@router.post("/stop")
async def stop_capture(background_tasks: BackgroundTasks):
    global _active_meeting_id, _capture_task
    if _active_meeting_id is None:
        raise HTTPException(status_code=409, detail="No active recording")
    meeting_id = _active_meeting_id
    if _capture_task:
        _capture_task.cancel()
        _capture_task = None
    capture.stop()
    _active_meeting_id = None
    await flush_buffer(meeting_id, broadcast)
    background_tasks.add_task(run_post_meeting, meeting_id)
    logger.info("Capture stopped for meeting %s — post-processing queued", meeting_id)
    return {"meeting_id": meeting_id, "status": "processing"}
