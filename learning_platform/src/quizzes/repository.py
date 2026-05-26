"""
Quiz and Question Repositories.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.repository import BaseRepository
from src.quizzes.models import Question, Quiz


class QuizRepository(BaseRepository[Quiz]):
    def __init__(self, session: AsyncSession):
        super().__init__(Quiz, session)

    async def get_by_lesson_id(self, lesson_id: UUID) -> Quiz | None:
        """Get quiz by lesson ID."""
        result = await self.session.execute(select(Quiz).where(Quiz.lesson_id == lesson_id))
        return result.scalar_one_or_none()


class QuestionRepository(BaseRepository[Question]):
    def __init__(self, session: AsyncSession):
        super().__init__(Question, session)

    async def list_by_quiz(self, quiz_id: UUID) -> list[Question]:
        """List all questions for a quiz."""
        result = await self.session.execute(
            select(Question).where(Question.quiz_id == quiz_id)
        )
        return list(result.scalars().all())

    async def count_by_quiz(self, quiz_id: UUID) -> int:
        """Count questions in a quiz."""
        result = await self.session.execute(
            select(func.count()).select_from(Question).where(Question.quiz_id == quiz_id)
        )
        return result.scalar_one()
