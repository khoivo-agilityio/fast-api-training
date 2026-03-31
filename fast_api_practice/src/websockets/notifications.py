"""WebSocket connection manager for real-time notifications."""

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections keyed by user_id.

    A single user may have multiple concurrent connections (e.g. two browser
    tabs). All of them receive every message sent to that user_id.
    """

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)
        logger.info("ws_connected", user_id=user_id)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)
        logger.info("ws_disconnected", user_id=user_id)

    async def send_to_user(self, user_id: int, data: dict) -> None:
        """Send a JSON payload to every active connection of *user_id*.

        Stale / broken sockets are silently pruned.
        """
        conns = list(self._connections.get(user_id, []))
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    @property
    def active_user_ids(self) -> list[int]:
        """Return the list of user IDs with at least one open connection."""
        return list(self._connections.keys())


# Module-level singleton — imported by both the router and tasks.py
manager = ConnectionManager()
