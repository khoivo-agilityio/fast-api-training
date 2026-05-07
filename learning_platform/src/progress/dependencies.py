"""
Progress Dependencies — FastAPI Depends() factories.

Provides dependency injection for ProgressService into route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.progress.service import ProgressService


def get_progress_service(db: AsyncSession = Depends(get_db)) -> ProgressService:
    """Dependency injection factory for ProgressService."""
    return ProgressService(db)
