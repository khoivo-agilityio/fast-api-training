"""API tags configuration."""

from enum import Enum


class Tags(Enum):
    """
    API endpoint tags as Enum.

    Benefits:
    - Type safety (can't misspell tags)
    - Auto-completion in IDE
    - Centralized tag management
    - Easy to refactor
    """

    AUTHENTICATION = "Authentication"
    USERS = "Users"
    ITEMS_PUBLIC = "Items (Public)"
    ITEMS_PROTECTED = "Items (Protected)"
    WEBSOCKET = "WebSocket"
    HEALTH = "Health & Monitoring"


# Metadata for OpenAPI documentation
tags_metadata = [
    {
        "name": Tags.AUTHENTICATION.value,
        "description": """
        **Authentication and authorization endpoints.**
        
        Operations:
        - Register new users
        - Login to get JWT token
        - Get current user information
        
        All protected endpoints require a valid JWT token in the `Authorization` header:
        ```
        Authorization: Bearer <your_token>
        ```
        """,
    },
    {
        "name": Tags.USERS.value,
        "description": """
        **User management operations.**
        
        Manage user accounts, profiles, and settings.
        Requires authentication for most operations.
        """,
    },
    {
        "name": Tags.ITEMS_PUBLIC.value,
        "description": """
        **Public item endpoints (no authentication required).**
        
        Browse and view published items without authentication.
        Limited to read-only operations on published content.
        """,
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://example.com/docs/items",
        },
    },
    {
        "name": Tags.ITEMS_PROTECTED.value,
        "description": """
        **Protected item endpoints (authentication required).**
        
        Full CRUD operations on items:
        - Create new items
        - Read all items (including your drafts)
        - Update your items
        - Delete your items
        
        **Authorization:**
        - You can only modify/delete your own items
        - You can view published items from all users
        - You can only see your own draft items
        """,
    },
    {
        "name": Tags.WEBSOCKET.value,
        "description": """
        **Real-time WebSocket communication.**
        
        Features:
        - Real-time chat
        - Live item updates
        - Online users tracking
        - System notifications
        
        **Authentication:**
        Connect using JWT token in URL:
        ```
        ws://localhost:8000/ws/{your_token}
        ```
        
        **Message Format:**
        ```json
        {
            "type": "message",
            "content": "Hello!",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        ```
        """,
        "externalDocs": {
            "description": "WebSocket Protocol Docs",
            "url": "https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API",
        },
    },
    {
        "name": Tags.HEALTH.value,
        "description": """
        **Health check and monitoring endpoints.**
        
        Monitor application status, performance, and diagnostics.
        """,
    },
]
