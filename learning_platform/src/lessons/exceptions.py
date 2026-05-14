"""Lesson module exceptions."""

from src.core.exceptions import NotFoundError


class LessonNotFound(NotFoundError):
    """Raised when a lesson is not found by ID."""

    def __init__(self, lesson_id: object = None):
        detail = f"Lesson not found: {lesson_id}" if lesson_id else "Lesson not found"
        super().__init__(detail=detail, error_code="LESSON_NOT_FOUND")
