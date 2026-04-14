from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.auth_service import AuthService
from src.infrastructure.background import simulate_welcome_email
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
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(_get_auth_service),
):
    user = await service.register(
        username=body.username,
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    background_tasks.add_task(
        simulate_welcome_email,
        user_id=user.id,
        username=user.username,
        email=user.email,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(_get_auth_service),
):
    return await service.login(username=form_data.username, password=form_data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshTokenRequest,
    service: AuthService = Depends(_get_auth_service),
):
    return await service.refresh(refresh_token=body.refresh_token)
