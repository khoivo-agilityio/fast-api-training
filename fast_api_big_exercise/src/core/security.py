"""Security utilities for password hashing and JWT token management.

This module provides:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- Token payload extraction
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from .config import get_settings

# ============================================================================
# PASSWORD HASHING
# ============================================================================


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string

    Example:
        >>> hashed = hash_password("mysecret123")
        >>> print(hashed)
        $2b$12$KIXl7Ks...  # bcrypt hash
    """
    # Convert password to bytes
    password_bytes = password.encode("utf-8")
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = hash_password("mysecret123")
        >>> verify_password("mysecret123", hashed)
        True
        >>> verify_password("wrongpassword", hashed)
        False
    """
    # Convert to bytes
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    # Verify password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ============================================================================
# JWT TOKEN MANAGEMENT
# ============================================================================


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Payload data to encode in the token (e.g., {"sub": "user123"})
        expires_delta: Optional custom expiration time. If None, uses settings default.

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token({"sub": "john@example.com"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

        >>> # Custom expiration
        >>> token = create_access_token(
        ...     {"sub": "john@example.com"},
        ...     expires_delta=timedelta(hours=1)
        ... )
    """
    settings = get_settings()

    # Create a copy to avoid modifying the original data
    to_encode = data.copy()

    # Calculate expiration time
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add expiration to payload
    to_encode.update({"exp": expire})

    # Encode and return JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    # jwt.encode may return bytes in some PyJWT versions; ensure we return a str
    if isinstance(encoded_jwt, bytes):
        encoded_jwt = encoded_jwt.decode("utf-8")

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid (bad signature, malformed, etc.)

    Example:
        >>> token = create_access_token({"sub": "john@example.com"})
        >>> payload = decode_access_token(token)
        >>> print(payload["sub"])
        john@example.com

        >>> # Handle expired token
        >>> try:
        ...     payload = decode_access_token(expired_token)
        ... except jwt.ExpiredSignatureError:
        ...     print("Token expired")
        ... except jwt.InvalidTokenError:
        ...     print("Invalid token")
    """
    settings = get_settings()

    # Decode and validate JWT
    # This will automatically check:
    # - Signature is valid
    # - Token hasn't expired (exp claim)
    # - Token structure is correct
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    return payload


def extract_token_subject(token: str) -> str | None:
    """Extract the subject (sub) claim from a JWT token.

    Args:
        token: JWT token string

    Returns:
        Subject string if valid, None if token is invalid or expired

    Example:
        >>> token = create_access_token({"sub": "john@example.com"})
        >>> subject = extract_token_subject(token)
        >>> print(subject)
        john@example.com

        >>> # Invalid token returns None
        >>> subject = extract_token_subject("invalid_token")
        >>> print(subject)
        None
    """
    try:
        payload = decode_access_token(token)
        subject: str | None = payload.get("sub")
        return subject
    except jwt.InvalidTokenError:
        # InvalidTokenError is the base class for all JWT errors
        # including ExpiredSignatureError, so this catches both
        return None
