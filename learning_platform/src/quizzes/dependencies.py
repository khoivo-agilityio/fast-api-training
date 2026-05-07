"""
Quiz Dependencies — FastAPI Depends() factories.

Provides dependency injection for QuizService into route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.quizzes.service import QuizService


def get_quiz_service(db: AsyncSession = Depends(get_db)) -> QuizService:
    """Dependency injection factory for QuizService."""
    return QuizService(db)
