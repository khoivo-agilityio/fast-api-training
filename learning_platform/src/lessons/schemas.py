"""
Lesson Schemas (DTOs) — Pydantic v2.

Request/response models for lesson CRUD endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LessonCreateRequest(BaseModel):
    """Create a new lesson — POST /courses/{course_id}/lessons."""

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    timeline: str | None = None
    order: int = 0


class LessonUpdateRequest(BaseModel):
    """Partial update — PATCH /lessons/{id}."""

    title: str | None = Field(None, min_length=1, max_length=255)
    content: str | None = None
    timeline: str | None = None
    order: int | None = None


class LessonResponse(BaseModel):
    """Lesson response — returned by all lesson endpoints."""

    id: UUID
    course_id: UUID
    title: str
    timeline: str | None
    content: str
    order: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}
