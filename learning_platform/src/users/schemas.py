"""
User Schemas (DTOs) — Pydantic v2.

Request/response models for user profile endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserResponse(BaseModel):
    """User profile response — returned by GET /users/me."""

    id: UUID
    email: EmailStr
    role: str
    display_name: str
    avatar: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    """User profile update — used by PATCH /users/me."""

    display_name: str | None = None
    avatar: str | None = None
    password: str | None = Field(None, min_length=8, max_length=128)
