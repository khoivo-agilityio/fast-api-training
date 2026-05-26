"""
JWT Token Management — encode/decode access + refresh tokens.

Uses PyJWT for token creation and verification.
Token configuration (secret, algorithm, TTLs) comes from src.config.settings.
"""

import uuid
from datetime import UTC, datetime, timedelta

import jwt

from src.config import settings


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived access token."""
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, role: str) -> str:
    """Create a long-lived refresh token."""
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_token_pair(user_id: str, role: str) -> dict[str, str]:
    """Create both access and refresh tokens for a user."""
    return {
        "access_token": create_access_token(user_id, role),
        "refresh_token": create_refresh_token(user_id, role),
        "token_type": "bearer",
    }


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Raises:
        jwt.ExpiredSignatureError: Token has expired.
        jwt.InvalidTokenError: Token is malformed or has invalid signature.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
