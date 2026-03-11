"""Database connection setup."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import settings
from src.infrastructure.database.models import Base

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database (create tables)."""
    Base.metadata.create_all(bind=engine)


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
