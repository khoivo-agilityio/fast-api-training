"""User Pydantic schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username (3-50 characters)",
        examples=["john_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["john@example.com"],
    )
    full_name: str | None = Field(
        None,
        max_length=100,
        description="User's full name",
        examples=["John Doe"],
    )


class UserCreate(UserBase):
    """Schema for user registration request."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (8-100 characters)",
        examples=["SecurePass123!"],
    )


class UserUpdate(BaseModel):
    """Schema for user update request (all fields optional)."""

    email: EmailStr | None = Field(
        None,
        description="New email address",
    )
    full_name: str | None = Field(
        None,
        max_length=100,
        description="New full name",
    )
    password: str | None = Field(
        None,
        min_length=8,
        max_length=100,
        description="New password (8-100 characters)",
    )


class UserResponse(UserBase):
    """Schema for user response (returned to client)."""

    id: int = Field(..., description="User ID", examples=[1])
    is_active: bool = Field(..., description="Whether user account is active", examples=[True])
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = {"from_attributes": True}


class UserInDB(UserBase):
    """Schema for user data as stored in database (internal use)."""

    id: int
    hashed_password: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
