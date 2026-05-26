"""
Lesson Repository.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from src.lessons.models import Lesson


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, session: AsyncSession):
        super().__init__(Lesson, session)

    async def list_by_course(self, course_id: UUID) -> list[Lesson]:
        """List all lessons in a course, ordered by the 'order' field."""
        result = await self.session.execute(
            select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.order)
        )
        return list(result.scalars().all())

    async def count_by_course(self, course_id: UUID) -> int:
        """Count total lessons in a course."""
        result = await self.session.execute(
            select(func.count()).select_from(Lesson).where(Lesson.course_id == course_id)
        )
        return result.scalar_one()
