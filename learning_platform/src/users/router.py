"""
User Router — /api/v1/users endpoints.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user, require_roles
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


# ---------------------------------------------------------------------------
# Admin-only endpoints — /api/v1/admin/users/*
# ---------------------------------------------------------------------------

admin_router = APIRouter(prefix="/admin/users", tags=["admin"])


@admin_router.get("", response_model=list[UserResponse])
async def admin_list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_roles("admin")),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """List all users (admin only)."""
    users = await service.list_all(limit=limit, offset=offset)
    return [UserResponse.model_validate(u) for u in users]


@admin_router.get("/{user_id}", response_model=UserResponse)
async def admin_get_user(
    user_id: UUID,
    _: None = Depends(require_roles("admin")),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get any user by ID (admin only)."""
    user = await service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@admin_router.patch("/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    _: None = Depends(require_roles("admin")),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update any user's profile (admin only)."""
    user = await service.update_profile(user_id, data)
    return UserResponse.model_validate(user)


@admin_router.delete("/{user_id}", status_code=204)
async def admin_delete_user(
    user_id: UUID,
    _: None = Depends(require_roles("admin")),
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete a user (admin only)."""
    await service.delete(user_id)
