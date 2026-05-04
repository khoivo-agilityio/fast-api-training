"""
Auth Dependencies — FastAPI Depends() factories.

Provides:
- get_current_user: Extract and validate JWT from Authorization header
- require_roles: Factory that returns a dependency checking user role
- get_auth_service: DI factory for AuthService
"""

from uuid import UUID

import jwt as pyjwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import jwt
from src.auth.exceptions import (
    InsufficientPermissions,
    TokenExpired,
    TokenInvalid,
    TokenRevoked,
)
from src.auth.service import AuthService
from src.database import get_db
from src.redis import is_token_blacklisted
from src.users.models import User
from src.users.service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract user from JWT access token in the Authorization header.

    Validates the token, checks blacklist, and returns the User ORM instance.

    Raises:
        TokenExpired: If token has expired.
        TokenInvalid: If token is malformed or not an access token.
        TokenRevoked: If token JTI is in the Redis blacklist.
    """
    try:
        payload = jwt.decode_token(token)
    except pyjwt.ExpiredSignatureError:
        raise TokenExpired() from None
    except pyjwt.InvalidTokenError:
        raise TokenInvalid() from None

    if payload.get("type") != "access":
        raise TokenInvalid()

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise TokenRevoked()

    user_id = payload.get("sub")
    if not user_id:
        raise TokenInvalid()

    user_service = UserService(db)
    user = await user_service.get_by_id(UUID(user_id))
    return user


def require_roles(*roles: str):
    """Factory that returns a dependency checking the user has one of the given roles.

    Usage:
        @router.post("/courses", dependencies=[Depends(require_roles("instructor", "admin"))])
        async def create_course(...):
            ...
    """

    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise InsufficientPermissions(list(roles))
        return current_user

    return _check_role


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency injection factory for AuthService."""
    return AuthService(db)
