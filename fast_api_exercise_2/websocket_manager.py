"""WebSocket connection manager for real-time features."""

import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections.

    Features:
    - Track active connections
    - Broadcast messages to all clients
    - Send messages to specific clients
    - Handle disconnections
    """

    def __init__(self):
        # Store active connections: {user_id: WebSocket}
        self.active_connections: dict[int, WebSocket] = {}
        # Store connection metadata
        self.connection_metadata: dict[int, dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, user_id: int, username: str) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            user_id: User ID
            username: Username
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.connection_metadata[user_id] = {
            "username": username,
            "connected_at": datetime.utcnow().isoformat(),
        }
        logger.info(
            f"✅ User {username} (ID: {user_id}) connected. Total: {len(self.active_connections)}"
        )

        # Notify others about new connection
        await self.broadcast_system_message(
            f"{username} joined the chat", exclude_user_id=user_id
        )

    def disconnect(self, user_id: int) -> None:
        """
        Remove a WebSocket connection.

        Args:
            user_id: User ID to disconnect
        """
        if user_id in self.active_connections:
            username = self.connection_metadata[user_id]["username"]
            del self.active_connections[user_id]
            del self.connection_metadata[user_id]
            logger.info(
                f"❌ User {username} (ID: {user_id}) disconnected. Total: {len(self.active_connections)}"
            )

    async def send_personal_message(self, message: dict, user_id: int) -> None:
        """
        Send message to a specific user.

        Args:
            message: Message data (will be JSON serialized)
            user_id: Target user ID
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                self.disconnect(user_id)

    async def broadcast(
        self, message: dict, exclude_user_id: int | None = None
    ) -> None:
        """
        Broadcast message to all connected users.

        Args:
            message: Message data (will be JSON serialized)
            exclude_user_id: Optional user ID to exclude from broadcast
        """
        disconnected_users = []

        for user_id, websocket in self.active_connections.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id)

    async def broadcast_system_message(
        self, text: str, exclude_user_id: int | None = None
    ) -> None:
        """
        Broadcast a system message.

        Args:
            text: System message text
            exclude_user_id: Optional user ID to exclude
        """
        message = {
            "type": "system",
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast(message, exclude_user_id)

    async def notify_item_created(
        self, item_id: int, item_title: str, owner_username: str
    ) -> None:
        """
        Notify all users about a new item.

        Args:
            item_id: Created item ID
            item_title: Item title
            owner_username: Username of creator
        """
        message = {
            "type": "item_created",
            "item_id": item_id,
            "item_title": item_title,
            "owner_username": owner_username,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast(message)

    async def notify_item_updated(
        self, item_id: int, item_title: str, owner_username: str, changes: dict
    ) -> None:
        """
        Notify all users about an item update.

        Args:
            item_id: Updated item ID
            item_title: Item title
            owner_username: Username of owner
            changes: Dictionary of changed fields
        """
        message = {
            "type": "item_updated",
            "item_id": item_id,
            "item_title": item_title,
            "owner_username": owner_username,
            "changes": changes,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast(message)

    def get_online_users(self) -> list[dict[str, Any]]:
        """
        Get list of currently connected users.

        Returns:
            List of user information
        """
        return [
            {
                "user_id": user_id,
                "username": metadata["username"],
                "connected_at": metadata["connected_at"],
            }
            for user_id, metadata in self.connection_metadata.items()
        ]


# Global connection manager instance
manager = ConnectionManager()
