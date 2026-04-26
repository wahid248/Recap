from contextlib import asynccontextmanager

import aiosqlite

from config import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)

_CREATE_MEETINGS = """
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'recording',
    audio_path TEXT
);
"""

_CREATE_SEGMENTS = """
CREATE TABLE IF NOT EXISTS segments (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id),
    speaker TEXT NOT NULL,
    text TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    confidence REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_CREATE_SEGMENTS_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS segments_fts USING fts5(
    text, content='segments', content_rowid='rowid'
);
"""

_CREATE_SUMMARIES = """
CREATE TABLE IF NOT EXISTS summaries (
    meeting_id TEXT PRIMARY KEY REFERENCES meetings(id),
    overview TEXT NOT NULL,
    key_points TEXT NOT NULL,
    action_items TEXT NOT NULL,
    generated_at TEXT NOT NULL
);
"""

_FTS_INSERT_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS segments_ai AFTER INSERT ON segments BEGIN
    INSERT INTO segments_fts(rowid, text) VALUES (new.rowid, new.text);
END;
"""

_FTS_DELETE_TRIGGER = """
CREATE TRIGGER IF NOT EXISTS segments_ad AFTER DELETE ON segments BEGIN
    INSERT INTO segments_fts(segments_fts, rowid, text) VALUES('delete', old.rowid, old.text);
END;
"""


async def init_db() -> None:
    """Create all tables, FTS index, and triggers if they don't already exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_MEETINGS)
        await db.execute(_CREATE_SEGMENTS)
        await db.execute(_CREATE_SEGMENTS_FTS)
        await db.execute(_CREATE_SUMMARIES)
        await db.execute(_FTS_INSERT_TRIGGER)
        await db.execute(_FTS_DELETE_TRIGGER)
        await db.commit()
    logger.info("Database initialized at %s", DB_PATH)


@asynccontextmanager
async def get_db():
    """Async context manager yielding an open database connection."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db
