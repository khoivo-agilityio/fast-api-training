"""
Submission Dependencies — FastAPI Depends() factories.

Provides dependency injection for SubmissionService and its collaborators.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.courses.service import CourseService
from src.lessons.service import LessonService
from src.progress.service import ProgressService
from src.quizzes.service import QuizService
from src.submissions.service import SubmissionService


def get_submission_service(db: AsyncSession = Depends(get_db)) -> SubmissionService:
    """Dependency injection factory for SubmissionService."""
    return SubmissionService(db)


def get_quiz_service(db: AsyncSession = Depends(get_db)) -> QuizService:
    """Dependency injection factory for QuizService."""
    return QuizService(db)


def get_lesson_service_for_submissions(db: AsyncSession = Depends(get_db)) -> LessonService:
    """Dependency injection factory for LessonService (used by submissions)."""
    return LessonService(db)


def get_course_service_for_submissions(db: AsyncSession = Depends(get_db)) -> CourseService:
    """Dependency injection factory for CourseService (used by submissions)."""
    return CourseService(db)


def get_progress_service_for_submissions(db: AsyncSession = Depends(get_db)) -> ProgressService:
    """Dependency injection factory for ProgressService (used by submissions)."""
    return ProgressService(db)
