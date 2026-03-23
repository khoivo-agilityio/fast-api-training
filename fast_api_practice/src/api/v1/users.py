from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.domain.entities.user import UserEntity
from src.domain.services.user_service import UserService
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories import SQLAlchemyUserRepository
from src.schemas.user import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])


def _get_user_service(
    session: AsyncSession = Depends(get_async_session),
) -> UserService:
    return UserService(user_repo=SQLAlchemyUserRepository(session))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserEntity = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
):
    try:
        updated = await service.update_profile(
            user_id=current_user.id,
            full_name=body.full_name,
            email=body.email,
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    return updated
