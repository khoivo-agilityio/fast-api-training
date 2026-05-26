"""
Progress Repository — only queries the `progress` table.

Cross-domain data (lesson counts, enrolled courses) is fetched by calling
public methods on LessonService and CourseService respectively, following
the rule that each repository only touches its own domain's table.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from src.progress.models import Progress, ProgressStatus


class ProgressRepository(BaseRepository[Progress]):
    def __init__(self, session: AsyncSession):
        super().__init__(Progress, session)

    async def get_by_user_and_lesson(self, user_id: UUID, lesson_id: UUID) -> Progress | None:
        """Get progress record for a (user, lesson) pair."""
        result = await self.session.execute(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.lesson_id == lesson_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_completed_in_lessons(
        self, user_id: UUID, lesson_ids: list[UUID]
    ) -> int:
        """Count completed progress records for a given set of lesson IDs."""
        if not lesson_ids:
            return 0
        result = await self.session.execute(
            select(Progress)
            .where(
                Progress.user_id == user_id,
                Progress.status == ProgressStatus.COMPLETED,
                Progress.lesson_id.in_(lesson_ids),
            )
        )
        return len(result.scalars().all())

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Progress]:
        """List all progress records with pagination."""
        result = await self.session.execute(
            select(Progress).order_by(Progress.accessed_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
