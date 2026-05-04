"""
User Dependencies — FastAPI Depends() factories.

Provides dependency injection for UserService into route handlers.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.users.service import UserService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency injection factory for UserService."""
    return UserService(db)
