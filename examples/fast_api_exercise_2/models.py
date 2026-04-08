"""Database models for users and items."""

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class ItemStatus(str, Enum):
    """Item status enum."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


# ============================================================================
# USER MODELS
# ============================================================================


class User(SQLModel, table=True):
    """User database model."""

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    full_name: str | None = None
    hashed_password: str
    disabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# ITEM MODELS
# ============================================================================


class Item(SQLModel, table=True):
    """Item database model."""

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    price: float = Field(gt=0)
    status: ItemStatus = Field(default=ItemStatus.DRAFT)
    owner_id: int = Field(foreign_key="user.id")  # Link to User
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
