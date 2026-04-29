"""User request/response schemas (Pydantic v2)."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """User profile response."""

    id: uuid.UUID
    email: str
    role: str
    display_name: str
    avatar: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """Partial update payload for user profile."""

    display_name: str | None = None
    avatar: str | None = None
    password: str | None = None
