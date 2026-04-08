"""Pydantic schemas for request/response validation."""

from datetime import datetime

from models import ItemStatus
from pydantic import BaseModel, EmailStr, Field

# ============================================================================
# USER SCHEMAS
# ============================================================================


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    """Schema for user response (no password)."""

    id: int
    disabled: bool
    created_at: datetime


class UserInDB(UserBase):
    """User in database with hashed password."""

    id: int
    hashed_password: str
    disabled: bool


# ============================================================================
# TOKEN SCHEMAS
# ============================================================================


class Token(BaseModel):
    """OAuth2 token response."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""

    username: str | None = None


# ============================================================================
# ITEM SCHEMAS
# ============================================================================


class ItemBase(BaseModel):
    """Base item schema."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    price: float = Field(..., gt=0)
    status: ItemStatus = ItemStatus.DRAFT


class ItemCreate(ItemBase):
    """Schema for creating an item."""

    pass


class ItemUpdate(BaseModel):
    """Schema for updating an item (all fields optional)."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    price: float | None = Field(None, gt=0)
    status: ItemStatus | None = None


class ItemResponse(ItemBase):
    """Schema for item response."""

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
