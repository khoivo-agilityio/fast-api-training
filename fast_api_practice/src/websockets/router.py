"""WebSocket route: GET /ws/notifications?token=<jwt>"""

import jwt as pyjwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.core.security import decode_token
from src.websockets.notifications import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/notifications")
async def ws_notifications(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """Real-time notification stream.

    Connect with a valid access token::

        ws://host/ws/notifications?token=<jwt>

    The server pushes JSON objects when:
    - A task assigned to you changes status:
      ``{"type": "task_status_changed", "task_id": ..., "new_status": ..., ...}``

    The connection is kept alive until the client disconnects.
    """
    # ── 1. Authenticate ───────────────────────────────────────────────────────
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return
        user_id = int(payload["sub"])
    except (pyjwt.PyJWTError, KeyError, ValueError):
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # ── 2. Register connection ────────────────────────────────────────────────
    await manager.connect(user_id, websocket)

    # ── 3. Keep alive — drain incoming frames to detect disconnect ────────────
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
