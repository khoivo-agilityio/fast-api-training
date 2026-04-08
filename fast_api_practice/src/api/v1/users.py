from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_current_user, get_user_service
from src.domain.entities.user import UserEntity
from src.domain.services.user_service import UserService
from src.schemas.user import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserEntity = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    body: UserUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
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
