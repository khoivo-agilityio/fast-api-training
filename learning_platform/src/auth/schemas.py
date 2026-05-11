"""
Auth Schemas (DTOs) — Pydantic v2.

Request/response models for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Registration request — POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "alice@example.com",
                "password": "SecurePass123!",
                "display_name": "Alice Smith",
            }
        }
    }


class LoginRequest(BaseModel):
    """Login request — POST /auth/login."""

    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "alice@example.com",
                "password": "SecurePass123!",
            }
        }
    }


class TokenResponse(BaseModel):
    """Token pair response — returned after login, register, and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Token refresh request — POST /auth/refresh."""

    refresh_token: str
