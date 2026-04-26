import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from utils.logger import get_logger

router = APIRouter(tags=["websocket"])
logger = get_logger(__name__)

_connections: set[WebSocket] = set()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _connections.add(websocket)
    logger.info("WebSocket client connected (%d total)", len(_connections))
    try:
        while True:
            await websocket.receive_text()  # keep-alive; client sends nothing meaningful
    except WebSocketDisconnect:
        _connections.discard(websocket)
        logger.info("WebSocket client disconnected (%d total)", len(_connections))


async def broadcast(data: dict[str, Any]) -> None:
    """Send a JSON message to every connected WebSocket client."""
    if not _connections:
        return
    message = json.dumps(data)
    dead: set[WebSocket] = set()
    for ws in _connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)
