"""Database configuration and session management."""

from sqlmodel import Session, SQLModel, create_engine

# SQLite database for simplicity (use PostgreSQL in production)
DATABASE_URL = "sqlite:///./exercise2.db"

# Create engine with connection args for SQLite
connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables():
    """Create database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session
