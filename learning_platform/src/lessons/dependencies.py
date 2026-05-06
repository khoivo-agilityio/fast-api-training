"""
Lesson Dependencies — FastAPI Depends() factories.

Provides dependency injection for LessonService into route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.lessons.service import LessonService


def get_lesson_service(db: AsyncSession = Depends(get_db)) -> LessonService:
    """Dependency injection factory for LessonService."""
    return LessonService(db)
