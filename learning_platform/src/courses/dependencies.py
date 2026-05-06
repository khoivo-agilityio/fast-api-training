"""
Course Dependencies — FastAPI Depends() factories.

Provides dependency injection for CourseService into route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.courses.service import CourseService
from src.database import get_db


def get_course_service(db: AsyncSession = Depends(get_db)) -> CourseService:
    """Dependency injection factory for CourseService."""
    return CourseService(db)
