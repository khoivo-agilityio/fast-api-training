"""
Course and Enrollment Repositories.
"""

from typing import Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from src.courses.models import Course, Enrollment


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession):
        super().__init__(Course, session)

    async def list_courses(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        instructor_id: UUID | None = None,
    ) -> Tuple[list[Course], int]:
        query = select(Course)
        count_query = select(func.count()).select_from(Course)

        if search:
            query = query.where(Course.title.ilike(f"%{search}%"))
            count_query = count_query.where(Course.title.ilike(f"%{search}%"))
        if instructor_id:
            query = query.where(Course.instructor_id == instructor_id)
            count_query = count_query.where(Course.instructor_id == instructor_id)

        query = query.order_by(Course.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        total_result = await self.session.execute(count_query)

        return list(result.scalars().all()), total_result.scalar_one()


class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, session: AsyncSession):
        super().__init__(Enrollment, session)

    async def get_enrollment(self, user_id: UUID, course_id: UUID) -> Enrollment | None:
        result = await self.session.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id, Enrollment.course_id == course_id
            )
        )
        return result.scalar_one_or_none()

    async def get_enrolled_course_ids(self, user_id: UUID) -> list[UUID]:
        """Return all course IDs the user is enrolled in."""
        result = await self.session.execute(
            select(Enrollment.course_id).where(Enrollment.user_id == user_id)
        )
        return list(result.scalars().all())
