"""
Auth Service — Authentication & Token Management.

Class-based service pattern (per code review feedback, Issue #3):
"Should create a class and add all service functions to it?"

Answer: Yes — class-based services provide:
- Better testability (mock the class in tests)
- Shared session via constructor
- Clear API surface for cross-module calls
- Dependency injection via Depends() factory

This service handles registration, login, token refresh, and logout.
It delegates password operations to auth.security (async bcrypt)
and user CRUD to users.service.UserService.
"""

from datetime import UTC, datetime

import jwt as pyjwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt, security
from src.auth.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    TokenExpired,
    TokenInvalid,
    TokenRevoked,
)
from src.auth.models import BlacklistedToken
from src.auth.repository import BlacklistedTokenRepository
from src.auth.schemas import RegisterRequest, TokenResponse
from src.users.service import UserService


class AuthService:
    """Handles registration, login, token refresh, and logout."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._user_service = UserService(db)
        self._token_repo = BlacklistedTokenRepository(db)

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token's JTI is in the blacklist."""
        return await self._token_repo.is_blacklisted(jti)

    async def _blacklist_token(self, jti: str, expires_at: datetime) -> None:
        """Add a token's JTI to the blacklist."""
        token_record = BlacklistedToken(jti=jti, expires_at=expires_at)
        self._token_repo.add(token_record)
        await self._db.flush()

    async def register(self, data: RegisterRequest) -> TokenResponse:
        """Register a new user and return access + refresh tokens.

        Raises:
            EmailAlreadyRegistered: If the email is already in use.
        """
        existing = await self._user_service.get_by_email(data.email)
        if existing:
            raise EmailAlreadyRegistered(data.email)

        user = await self._user_service.create_user(
            email=data.email,
            password=data.password,
            display_name=data.display_name or "",
        )

        tokens = jwt.create_token_pair(str(user.id), user.role)
        return TokenResponse(**tokens)

    async def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate user by email/password and return tokens.

        Raises:
            InvalidCredentials: If email is not found or password is wrong.
        """
        user = await self._user_service.get_by_email(email)
        if not user:
            raise InvalidCredentials()

        if not await security.verify_password(password, user.password):
            raise InvalidCredentials()

        tokens = jwt.create_token_pair(str(user.id), user.role)
        return TokenResponse(**tokens)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Rotate tokens — verify refresh token, blacklist old, issue new pair.

        Raises:
            TokenExpired: If the refresh token has expired.
            TokenInvalid: If the refresh token is malformed.
            TokenRevoked: If the refresh token has been blacklisted.
        """
        try:
            payload = jwt.decode_token(refresh_token)
        except pyjwt.ExpiredSignatureError:
            raise TokenExpired() from None
        except pyjwt.InvalidTokenError:
            raise TokenInvalid() from None

        if payload.get("type") != "refresh":
            raise TokenInvalid()

        jti = payload.get("jti")
        if not jti:
            raise TokenInvalid()

        # Check if this refresh token has been revoked
        if await self._is_token_blacklisted(jti):
            raise TokenRevoked()

        # Blacklist the old refresh token (rotation)
        exp_timestamp = payload.get("exp", 0)
        expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)
        await self._blacklist_token(jti, expires_at)

        # Issue new token pair — role is already in the refresh payload, no DB hit needed
        user_id = payload["sub"]
        role = payload.get("role", "student")
        tokens = jwt.create_token_pair(user_id, role)
        return TokenResponse(**tokens)

    async def logout(self, access_token: str) -> None:
        """Logout — blacklist the access token so it cannot be reused.

        Raises:
            TokenInvalid: If the token cannot be decoded.
        """
        try:
            payload = jwt.decode_token(access_token)
        except pyjwt.ExpiredSignatureError:
            # Already expired — no need to blacklist
            return
        except pyjwt.InvalidTokenError:
            raise TokenInvalid() from None

        jti = payload.get("jti")
        if jti:
            exp_timestamp = payload.get("exp", 0)
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)
            await self._blacklist_token(jti, expires_at)
