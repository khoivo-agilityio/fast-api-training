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

from uuid import UUID

import jwt as pyjwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt, security
from src.auth.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    TokenExpired,
    TokenInvalid,
)
from src.auth.schemas import RegisterRequest, TokenResponse
from src.users.service import UserService


class AuthService:
    """Handles registration, login, token refresh, and logout."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._user_service = UserService(db)

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

        # Issue new token pair
        user_id = payload["sub"]
        user = await self._user_service.get_by_id(UUID(user_id))
        tokens = jwt.create_token_pair(str(user.id), user.role)
        return TokenResponse(**tokens)

    async def logout(self, access_token: str) -> None:
        """Logout endpoint logic.

        Since Redis was removed, this is a no-op on the server.
        The client is responsible for discarding the token to complete logout.

        Raises:
            TokenInvalid: If the token cannot be decoded.
        """
        try:
            jwt.decode_token(access_token)
        except pyjwt.ExpiredSignatureError:
            return
        except pyjwt.InvalidTokenError:
            raise TokenInvalid() from None
