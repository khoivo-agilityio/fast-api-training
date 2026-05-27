"""
Course Schemas (DTOs) — Pydantic v2.

Request/response models for course CRUD and enrollment endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CourseCreateRequest(BaseModel):
    """Create a new course — POST /courses."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Introduction to Python",
                "description": (
                    "A beginner-friendly Python course covering syntax, data structures, and OOP."
                ),
            }
        }
    }


class CourseUpdateRequest(BaseModel):
    """Partial update — PATCH /courses/{id}."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None


class CourseResponse(BaseModel):
    """Course response — returned by all course endpoints."""

    id: UUID
    title: str
    description: str | None
    instructor_id: UUID
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    """Paginated list of courses."""

    items: list[CourseResponse]
    total: int
    limit: int
    offset: int


class EnrollmentResponse(BaseModel):
    """Enrollment response — returned by POST /courses/{id}/enroll."""

    id: UUID
    user_id: UUID
    course_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
