"""JWT access and refresh token creation and validation."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.config import settings


def create_access_token(user_id: str, role: str) -> str:
    """Create a JWT access token with user_id, role, and JTI."""
    return _create_token(
        {"sub": user_id, "role": role, "type": "access"},
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token with user_id and JTI."""
    return _create_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def _create_token(payload: dict[str, Any], expire_delta: timedelta) -> str:
    """Internal helper to create a signed JWT with expiration and JTI."""
    data = payload.copy()
    data["exp"] = datetime.now(UTC) + expire_delta
    data["iat"] = datetime.now(UTC)
    data["jti"] = str(uuid.uuid4())
    return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
