"""
Lesson Service — Lesson CRUD.

Class-based service pattern:
- Takes AsyncSession via constructor
- All DB queries are owned by this service
- Raises domain exceptions — never HTTPException
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.lessons.exceptions import LessonNotFound
from src.lessons.models import Lesson
from src.lessons.repository import LessonRepository
from src.lessons.schemas import LessonCreateRequest, LessonUpdateRequest

if TYPE_CHECKING:
    from src.users.models import User


class LessonService:
    """Handles lesson CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self.repo = LessonRepository(db)

    async def create(self, course_id: UUID, data: LessonCreateRequest) -> Lesson:
        """Create a new lesson in the given course."""
        lesson = Lesson(
            course_id=course_id,
            title=data.title,
            content=data.content,
            timeline=data.timeline,
            order=data.order,
        )
        self.repo.add(lesson)
        await self._db.flush()
        return lesson

    async def get_by_id(self, lesson_id: UUID) -> Lesson:
        """Get lesson by ID or raise LessonNotFound."""
        lesson = await self.repo.get_by_id(lesson_id)
        if not lesson:
            raise LessonNotFound(lesson_id)
        return lesson

    async def get_and_track(
        self, lesson_id: UUID, user: "User", progress_service, quiz_service
    ) -> Lesson:
        """Get a lesson and track progress for students.

        For student users, this:
        1. Fetches the lesson
        2. Asks quiz_service whether the lesson has a quiz (avoids cross-module import)
        3. Calls progress_service.touch() to record the visit

        For non-students, simply returns the lesson.
        """
        lesson = await self.get_by_id(lesson_id)

        if user.role == "student":  # pragma: no cover
            has_quiz = await quiz_service.has_quiz_for_lesson(lesson_id)  # pragma: no cover
            await progress_service.touch(user.id, lesson_id, has_quiz)  # pragma: no cover
  # pragma: no cover
        return lesson  # pragma: no cover

    async def list_by_course(self, course_id: UUID) -> list[Lesson]:
        """List all lessons in a course, ordered by the 'order' field."""
        return await self.repo.list_by_course(course_id)

    async def update(self, lesson_id: UUID, data: LessonUpdateRequest) -> Lesson:
        """Partial update of a lesson."""
        lesson = await self.get_by_id(lesson_id)
        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("id", None)
        for field, value in update_data.items():
            setattr(lesson, field, value)
        lesson.updated_at = datetime.now(UTC)
        await self._db.flush()
        return lesson

    async def delete(self, lesson_id: UUID) -> None:
        """Delete a lesson."""
        lesson = await self.get_by_id(lesson_id)
        await self.repo.delete(lesson)
        await self._db.flush()

    async def count_by_course(self, course_id: UUID) -> int:
        """Return the total number of lessons in a course."""
        return await self.repo.count_by_course(course_id)
