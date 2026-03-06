"""WebSocket routes for real-time communication."""

import logging
from typing import Annotated

import jwt
from auth import ALGORITHM, SECRET_KEY
from database import get_session
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import HTMLResponse
from models import User
from sqlmodel import Session
from tags import Tags  # Import Tags enum
from websocket_manager import manager

# Use enum for tags
router = APIRouter(tags=[Tags.WEBSOCKET.value])

logger = logging.getLogger(__name__)


async def get_user_from_token(token: str, session: Session) -> User | None:
    """Validate JWT token and return user."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None

        from auth import get_user_by_username

        user = get_user_by_username(session, username)
        return user
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return None


@router.websocket("/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    session: Annotated[Session, Depends(get_session)],
) -> None:
    """
    WebSocket endpoint for real-time communication.

    **Authentication:**
    - Connect using JWT token in URL: `ws://localhost:8000/ws/{token}`

    **Message Types:**
    - `ping`: Keep-alive ping (responds with pong)
    - `message`: Chat message (broadcast or private)
    - `get_online_users`: Request list of online users

    **Example Message:**
    ```json
    {
        "type": "message",
        "content": "Hello World!",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    ```
    """
    # Validate token
    user = await get_user_from_token(token, session)
    if not user or user.disabled:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect user
    await manager.connect(websocket, user.id, user.username)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "welcome",
                "message": f"Welcome {user.username}!",
                "online_users": manager.get_online_users(),
            },
            user.id,
        )

        # Listen for messages
        while True:
            data = await websocket.receive_json()

            message_type = data.get("type", "message")

            if message_type == "ping":
                await manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")},
                    user.id,
                )

            elif message_type == "message":
                content = data.get("content", "")
                recipient_id = data.get("recipient_id")

                message = {
                    "type": "message",
                    "sender_id": user.id,
                    "sender_username": user.username,
                    "content": content,
                    "timestamp": data.get("timestamp"),
                }

                if recipient_id:
                    await manager.send_personal_message(message, recipient_id)
                    message["recipient_id"] = recipient_id
                    await manager.send_personal_message(message, user.id)
                else:
                    await manager.broadcast(message)

            elif message_type == "get_online_users":
                await manager.send_personal_message(
                    {
                        "type": "online_users",
                        "users": manager.get_online_users(),
                    },
                    user.id,
                )

            else:
                await manager.send_personal_message(
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    },
                    user.id,
                )

    except WebSocketDisconnect:
        manager.disconnect(user.id)
        await manager.broadcast_system_message(f"{user.username} left the chat")

    except Exception as e:
        logger.error(f"WebSocket error for user {user.username}: {e}")
        manager.disconnect(user.id)


@router.get(
    "/ws-test",
    summary="WebSocket test page",
    description="Interactive HTML page to test WebSocket connections",
    response_class=HTMLResponse,
)
async def get_websocket_test_page() -> HTMLResponse:
    """
    Simple HTML page to test WebSocket connection.

    **Usage:**
    1. Login to get a token: `POST /token`
    2. Open: http://localhost:8000/ws-test
    3. Enter your token and connect
    4. Start chatting!
    """
    # ... (same HTML content as before)
