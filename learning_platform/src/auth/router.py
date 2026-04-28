"""Auth router — POST /auth/{register, login, refresh, logout}."""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service as auth_service
from src.auth.dependencies import CurrentUser
from src.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from src.database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=201,
    summary="Register a new user",
    description="Create a new student account and return JWT token pair.",
)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.register(session, data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password. Returns JWT token pair.",
)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.login(session, data.email, data.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Exchange a valid refresh token for a new access + refresh token pair.",
)
async def refresh(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.refresh(session, data.refresh_token)


@router.post(
    "/logout",
    status_code=204,
    summary="Logout",
    description="Blacklist the current access token and invalidate the refresh token.",
)
async def logout(
    payload: CurrentUser,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> None:
    await auth_service.logout(credentials.credentials, payload["sub"])
