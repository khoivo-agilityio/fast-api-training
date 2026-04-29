"""Auth business logic — register, login, refresh, logout.

No repository layer: this service queries the DB directly via AsyncSession.
"""

import uuid
from datetime import timedelta

import jwt as pyjwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import InvalidCredentials, InvalidToken, TokenRevoked
from src.auth.jwt import create_access_token, create_refresh_token, decode_token
from src.auth.schemas import RegisterRequest, TokenResponse
from src.auth.security import hash_password, verify_password
from src.config import settings
from src.exceptions import ConflictError
from src.redis import (
    blacklist_token,
    delete_refresh_token,
    get_stored_refresh_token,
    is_token_blacklisted,
    store_refresh_token,
)
from src.users.models import User


async def register(session: AsyncSession, data: RegisterRequest) -> TokenResponse:
    """Register a new user and return token pair."""
    # Check duplicate email
    result = await session.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        password=hash_password(data.password),
        display_name=data.display_name or "",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return await _issue_tokens(user)


async def login(session: AsyncSession, email: str, password: str) -> TokenResponse:
    """Authenticate user and return token pair."""
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password):
        raise InvalidCredentials()
    return await _issue_tokens(user)


async def refresh(session: AsyncSession, refresh_token: str) -> TokenResponse:
    """Rotate tokens — validate refresh token, blacklist old, issue new pair."""
    try:
        payload = decode_token(refresh_token)
    except pyjwt.PyJWTError:
        raise InvalidToken("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise InvalidToken("Invalid token type")

    user_id = payload.get("sub")
    stored = await get_stored_refresh_token(user_id)
    if stored != refresh_token:
        raise TokenRevoked("Refresh token has been revoked or replaced")

    user = await session.get(User, uuid.UUID(user_id))
    if not user:
        raise InvalidToken("User not found")

    # Rotate: delete old refresh token, issue new pair
    await delete_refresh_token(user_id)
    return await _issue_tokens(user)


async def logout(access_token: str, user_id: str) -> None:
    """Blacklist the access token and delete the stored refresh token."""
    # Check if already blacklisted
    if await is_token_blacklisted(access_token):
        raise TokenRevoked("Token has already been revoked")

    ttl = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await blacklist_token(access_token, ttl)
    await delete_refresh_token(user_id)


async def _issue_tokens(user: User) -> TokenResponse:
    """Create access + refresh tokens and store refresh in Redis."""
    access_token = create_access_token(str(user.id), user.role)
    refresh_token = create_refresh_token(str(user.id))
    ttl = int(timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
    await store_refresh_token(str(user.id), refresh_token, ttl)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)
