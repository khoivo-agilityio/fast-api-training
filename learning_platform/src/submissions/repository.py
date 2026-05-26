"""
Submission and Answer Repositories.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.repository import BaseRepository
from src.submissions.models import Answer, Submission


class SubmissionRepository(BaseRepository[Submission]):
    def __init__(self, session: AsyncSession):
        super().__init__(Submission, session)

    async def get_by_user_and_quiz(self, user_id: UUID, quiz_id: UUID) -> Submission | None:
        """Get a user's submission for a specific quiz."""
        result = await self.session.execute(
            select(Submission).where(
                Submission.user_id == user_id, Submission.quiz_id == quiz_id
            )
        )
        return result.scalar_one_or_none()

    async def get_with_answers(self, user_id: UUID, quiz_id: UUID) -> Submission | None:
        """Get a submission with eagerly loaded answers using selectinload."""
        result = await self.session.execute(
            select(Submission)
            .options(selectinload(Submission.answers))
            .where(Submission.user_id == user_id, Submission.quiz_id == quiz_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Submission]:
        """List all submissions with pagination (admin use)."""
        result = await self.session.execute(
            select(Submission).order_by(Submission.submitted_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())


class AnswerRepository(BaseRepository[Answer]):
    def __init__(self, session: AsyncSession):
        super().__init__(Answer, session)
