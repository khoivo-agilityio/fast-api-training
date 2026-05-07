"""Progress Schemas (DTOs) — Pydantic v2."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LessonProgressResponse(BaseModel):
    """Single lesson progress record."""

    lesson_id: UUID
    status: str
    accessed_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CourseProgressResponse(BaseModel):
    """Derived course-level progress (computed, not stored)."""

    course_id: UUID
    course_title: str
    completed_lessons: int
    total_lessons: int
    percent_complete: float
    is_complete: bool
