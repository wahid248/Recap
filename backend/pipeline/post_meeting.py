from datetime import datetime, timezone

from storage.models import Summary
from storage.queries import get_segments, insert_summary, update_meeting_status
from summarization.summarizer import summarize
from utils.gpu import unload_all_models
from utils.logger import get_logger

logger = get_logger(__name__)


async def run(meeting_id: str) -> Summary:
    """Unload live models, generate an LLM summary, persist it, and mark meeting completed."""
    await update_meeting_status(meeting_id, "processing", datetime.now(timezone.utc).isoformat())

    # Free VRAM before loading the LLM
    unload_all_models()

    segments = await get_segments(meeting_id)
    transcript = "\n".join(f"{seg.speaker}: {seg.text}" for seg in segments)

    try:
        result = await summarize(transcript)
    except Exception:
        logger.exception("Summarization failed for meeting %s", meeting_id)
        result = {"overview": "Summary generation failed.", "key_points": [], "action_items": []}

    summary = Summary(
        meeting_id=meeting_id,
        overview=result["overview"],
        key_points=result.get("key_points", []),
        action_items=result.get("action_items", []),
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    await insert_summary(summary)
    await update_meeting_status(meeting_id, "completed")
    logger.info("Post-meeting processing complete for meeting %s", meeting_id)
    return summary
