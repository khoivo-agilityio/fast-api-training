from fastapi import APIRouter, Depends

from src.api.dependencies import get_current_user, get_user_service
from src.domain.entities.user import UserEntity
from src.domain.services.user_service import UserService
from src.schemas.common import PaginatedResponse, PaginationParams
from src.schemas.user import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    service: UserService = Depends(get_user_service),
):
    items, total = await service.list_users(
        limit=pagination.limit, offset=pagination.offset
    )
    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserEntity = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):
    return await service.update_profile(
        user_id=current_user.id,
        full_name=body.full_name,
        email=body.email,
        password=body.password,
    )
