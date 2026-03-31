from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# --- Request schemas ---


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["john_doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["Secur3P@ss!"])
    full_name: str | None = Field(None, max_length=100, examples=["John Doe"])


class UserLoginRequest(BaseModel):
    username: str = Field(..., examples=["john_doe"])
    password: str = Field(..., examples=["Secur3P@ss!"])


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., examples=["<your_refresh_token>"])


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(None, max_length=100, examples=["Jane Doe"])
    email: EmailStr | None = Field(None, examples=["jane@example.com"])
    password: str | None = Field(
        None, min_length=8, max_length=128, examples=["NewP@ss123!"]
    )


# --- Response schemas ---


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str | None
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
