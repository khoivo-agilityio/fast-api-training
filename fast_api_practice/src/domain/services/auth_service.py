import jwt

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from src.domain.entities.user import UserEntity
from src.domain.exceptions import AuthenticationError, ConflictError
from src.domain.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> UserEntity:
        if await self._user_repo.get_by_username(username):
            raise ConflictError("Username already taken")
        if await self._user_repo.get_by_email(email):
            raise ConflictError("Email already registered")
        hashed = hash_password(password)
        return await self._user_repo.create(
            username=username,
            email=email,
            hashed_password=hashed,
            full_name=full_name,
        )

    async def login(self, username: str, password: str) -> dict:
        user = await self._user_repo.get_by_username(username)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }

    async def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as e:
            raise AuthenticationError(str(e)) from e
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        user_id = int(payload["sub"])
        user = await self._user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or deactivated")
        return {
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "token_type": "bearer",
        }
