"""
Admin Auth — Dual authentication for admin UI helper endpoints.

These endpoints (e.g. /admin/ui/courses, /admin/ui/lessons) are called by
browser fetch from SQLAdmin pages. They need to accept either:
  1. JWT Bearer token with admin role (API clients), OR
  2. Valid SQLAdmin session cookie (browser calls from admin UI)
"""

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import InsufficientPermissions
from src.auth.jwt import decode_token
from src.core.database import get_db


async def require_admin_or_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Dual auth dependency — accepts JWT Bearer OR SQLAdmin session cookie.

    Tries JWT first. If no Bearer token is present, falls back to checking
    the SQLAdmin session for a valid admin token.

    Raises:
        InsufficientPermissions: If neither auth method succeeds.
    """
    # 1. Try JWT Bearer token
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        if token:
            try:
                payload = decode_token(token)
                if payload.get("type") == "access" and payload.get("role") == "admin":
                    return  # Authenticated via JWT
            except Exception:
                pass  # Fall through to session check

    # 2. Try SQLAdmin session cookie
    session_token = request.session.get("token") if hasattr(request, "session") else None
    if session_token:
        try:
            payload = decode_token(session_token)
            if payload.get("role") == "admin":
                return  # Authenticated via session
        except Exception:
            pass

    raise InsufficientPermissions(["admin"])
