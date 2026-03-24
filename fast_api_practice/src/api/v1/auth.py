import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.auth_service import AuthService
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories import SQLAlchemyUserRepository
from src.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    return AuthService(user_repo=SQLAlchemyUserRepository(session))


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: UserRegisterRequest,
    service: AuthService = Depends(_get_auth_service),
):
    try:
        user = await service.register(
            username=body.username,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(_get_auth_service),
):
    try:
        tokens = await service.login(
            username=form_data.username, password=form_data.password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshTokenRequest,
    service: AuthService = Depends(_get_auth_service),
):
    try:
        tokens = await service.refresh(refresh_token=body.refresh_token)
    except (ValueError, jwt.PyJWTError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    return tokens
