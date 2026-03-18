"""Database connection setup."""

from collections.abc import Generator

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings
from src.infrastructure.database.models import Base

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database (create tables).

    Used by tests which manage their own in-memory SQLite databases.
    Production startup should use ``run_migrations()`` instead.
    """
    Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    """Run Alembic migrations programmatically (upgrade to head).

    Safe to call on every startup — Alembic tracks applied revisions
    and only runs pending ones.
    """

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


def get_db() -> Generator[Session, None, None]:
    """
    Get database session dependency.

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
