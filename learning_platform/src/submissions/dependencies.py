"""
Submission Dependencies — FastAPI Depends() factories.

Provides dependency injection for SubmissionService into route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.submissions.service import SubmissionService


def get_submission_service(db: AsyncSession = Depends(get_db)) -> SubmissionService:
    """Dependency injection factory for SubmissionService."""
    return SubmissionService(db)
