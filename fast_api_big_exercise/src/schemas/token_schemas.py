"""JWT Token Pydantic schemas."""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
        examples=["bearer"],
    )


class TokenData(BaseModel):
    """Schema for decoded token payload data."""

    username: str | None = Field(
        None,
        description="Username from token subject",
        examples=["john_doe"],
    )
