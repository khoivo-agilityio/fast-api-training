"""Auth request/response schemas (Pydantic v2)."""

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str
    display_name: str | None = None


class LoginRequest(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token payload."""

    refresh_token: str
