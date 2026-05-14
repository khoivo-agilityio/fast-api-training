"""
Database — Async SQLAlchemy engine, session factory, and Base.

Usage:
    from src.core.database import get_db
    # In FastAPI dependencies: db: AsyncSession = Depends(get_db)
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


def _normalize_db_url(url: str) -> str:
    """Ensure the DATABASE_URL uses the asyncpg driver.

    Railway (and many PaaS providers) supply a plain ``postgresql://…`` URL.
    SQLAlchemy requires ``postgresql+asyncpg://…`` for async connections.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(_normalize_db_url(settings.DATABASE_URL), echo=settings.ENABLE_DEBUG)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session; auto-commit on success, rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
