"""Auth dependencies — get_current_user, require_roles."""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.exceptions import InvalidToken, TokenRevoked
from src.auth.jwt import decode_token
from src.redis import is_token_blacklisted

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    """Extract and validate the current user from the Bearer token.

    Returns the decoded JWT payload dict with keys: sub, role, type, exp, iat, jti.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise InvalidToken()

    if payload.get("type") != "access":
        raise InvalidToken("Invalid token type")

    if await is_token_blacklisted(token):
        raise TokenRevoked()

    return payload


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_roles(*roles: str):
    """Dependency factory that restricts access to users with specified roles.

    Usage: `payload: dict = require_roles("admin", "instructor")`
    """

    async def _check(payload: CurrentUser) -> dict:
        if payload.get("role") not in roles:
            from src.exceptions import AuthorizationError

            raise AuthorizationError("Insufficient permissions")
        return payload

    return Depends(_check)
