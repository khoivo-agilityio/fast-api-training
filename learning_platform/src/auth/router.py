"""
Auth Router — /api/v1/auth endpoints.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.auth.dependencies import get_auth_service, get_current_user, oauth2_scheme
from src.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from src.auth.service import AuthService
from src.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("3/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Register a new user account (defaults to student role)."""
    return await service.register(data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with email and password, returns access + refresh tokens."""
    return await service.login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_tokens(
    request: Request,
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    return await service.refresh(data.refresh_token)


@router.post("/logout", status_code=200)
async def logout(
    token: str = Depends(oauth2_scheme),
    _current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Logout — blacklists the access token so it cannot be reused."""
    await service.logout(token)
    return {"detail": "Successfully logged out"}  # pragma: no cover
