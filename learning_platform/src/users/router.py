"""
User Router — /api/v1/users endpoints.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.users.dependencies import get_user_service
from src.users.models import User
from src.users.schemas import UserResponse, UserUpdateRequest
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get the authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update the authenticated user's profile (partial update)."""
    updated = await service.update_profile(current_user.id, data)
    return UserResponse.model_validate(updated)
