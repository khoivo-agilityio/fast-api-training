"""
User Schemas (DTOs) — Pydantic v2.

Request/response models for user profile endpoints.
"""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


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

    @field_validator("avatar")
    @classmethod
    def validate_avatar_url(cls, v: str | None) -> str | None:
        """Ensure avatar URL points to a trusted S3 or MinIO storage origin."""
        if v is None:
            return v
        pattern = r"^https?://(.+\.s3(\..+)?\.amazonaws\.com|localhost:\d+|127\.0\.0\.1:\d+)/.+"
        if not re.match(pattern, v):
            raise ValueError(
                "Avatar URL must be a valid S3 or MinIO storage URL "
                "(e.g. https://bucket.s3.amazonaws.com/... or http://localhost:9000/...)"
            )
        return v
