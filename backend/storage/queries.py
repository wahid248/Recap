import json
from typing import Optional

from storage.database import get_db
from storage.models import Meeting, Segment, Summary


async def insert_meeting(meeting: Meeting) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT INTO meetings (id, title, started_at, ended_at, status, audio_path) VALUES (?,?,?,?,?,?)",
            (meeting.id, meeting.title, meeting.started_at, meeting.ended_at, meeting.status, meeting.audio_path),
        )
        await db.commit()


async def get_meeting(meeting_id: str) -> Optional[Meeting]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,))
        row = await cursor.fetchone()
        return Meeting(**dict(row)) if row else None


async def list_meetings() -> list[Meeting]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM meetings ORDER BY started_at DESC")
        rows = await cursor.fetchall()
        return [Meeting(**dict(r)) for r in rows]


async def update_meeting_status(meeting_id: str, status: str, ended_at: Optional[str] = None) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE meetings SET status = ?, ended_at = COALESCE(?, ended_at) WHERE id = ?",
            (status, ended_at, meeting_id),
        )
        await db.commit()


async def delete_meeting(meeting_id: str) -> None:
    async with get_db() as db:
        await db.execute("DELETE FROM segments WHERE meeting_id = ?", (meeting_id,))
        await db.execute("DELETE FROM summaries WHERE meeting_id = ?", (meeting_id,))
        await db.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        await db.commit()


async def insert_segment(segment: Segment) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT INTO segments (id, meeting_id, speaker, text, start_time, end_time, confidence) VALUES (?,?,?,?,?,?,?)",
            (segment.id, segment.meeting_id, segment.speaker, segment.text, segment.start_time, segment.end_time, segment.confidence),
        )
        await db.commit()


async def get_segments(meeting_id: str) -> list[Segment]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM segments WHERE meeting_id = ? ORDER BY start_time",
            (meeting_id,),
        )
        rows = await cursor.fetchall()
        return [Segment(**dict(r)) for r in rows]


async def insert_summary(summary: Summary) -> None:
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO summaries (meeting_id, overview, key_points, action_items, generated_at) VALUES (?,?,?,?,?)",
            (summary.meeting_id, summary.overview, json.dumps(summary.key_points), json.dumps(summary.action_items), summary.generated_at),
        )
        await db.commit()


async def get_summary(meeting_id: str) -> Optional[Summary]:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM summaries WHERE meeting_id = ?", (meeting_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["key_points"] = json.loads(d["key_points"])
        d["action_items"] = json.loads(d["action_items"])
        return Summary(**d)


async def search_segments(query: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT s.*, m.title, m.started_at
            FROM segments s
            JOIN segments_fts fts ON s.rowid = fts.rowid
            JOIN meetings m ON s.meeting_id = m.id
            WHERE segments_fts MATCH ?
            ORDER BY rank
            """,
            (query,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
