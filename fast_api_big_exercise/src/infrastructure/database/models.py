"""SQLAlchemy database models."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TaskStatus(str, Enum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserModel(Base):
    """User database model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tasks = relationship("TaskModel", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, username='{self.username}')>"


class TaskModel(Base):
    """Task database model."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=TaskStatus.TODO.value, nullable=False)
    priority = Column(String(20), default=TaskPriority.MEDIUM.value, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("UserModel", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<TaskModel(id={self.id}, title='{self.title}')>"
