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


import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

class AuditMixin:
    """Mixin to add audit fields to models."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=func.now()
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session."""
    async with async_session_factory() as session:
        yield session
