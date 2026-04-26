from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import capture, meetings, summary, ws
from config import HOST, PORT
from storage.database import init_db
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Recap backend listening on %s:%d", HOST, PORT)
    yield
    logger.info("Recap backend shutting down")


app = FastAPI(title="Recap", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tauri webview origin is not a standard browser origin
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meetings.router)
app.include_router(capture.router)
app.include_router(summary.router)
app.include_router(ws.router)
