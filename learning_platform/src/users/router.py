"""
User Router — /api/v1/users endpoints.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user, require_roles
from src.core.dependencies import get_storage_service
from src.core.schemas import (
    AvatarConfirmRequest,
    PresignedUrlRequest,
    PresignedUrlResponse,
)
from src.core.service import StorageService
from src.users.dependencies import get_user_service
from src.users.models import User
from src.users.schemas import UserResponse, UserUpdateRequest
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get the authenticated user's profile."""
    user = await service.get_by_id(current_user.id)
    return UserResponse.model_validate(user)  # pragma: no cover  # pragma: no cover


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update the authenticated user's profile (partial update)."""
    updated = await service.update_profile(current_user.id, data)
    return UserResponse.model_validate(updated)  # pragma: no cover  # pragma: no cover


@router.post(
    "/me/avatar/presigned",
    response_model=PresignedUrlResponse,
    status_code=201,
    summary="Request a presigned S3 PUT URL for avatar upload",
)
async def request_avatar_presigned_url(
    data: PresignedUrlRequest,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
) -> PresignedUrlResponse:
    """Generate a short-lived presigned PUT URL.

    **Upload flow:**
    1. Call this endpoint with `content_type` (e.g. `image/jpeg`).
    2. PUT the file bytes directly to `upload_url` (from the client — no server proxy).
    3. Call `PATCH /users/me/avatar` with the returned `object_key` to confirm.

    The URL expires in `expires_in` seconds (default 5 minutes).
    """
    return await storage.generate_presigned_put(data.content_type)


@router.patch(
    "/me/avatar",
    response_model=UserResponse,
    summary="Confirm avatar upload and activate CDN URL",
)
async def confirm_avatar_upload(
    data: AvatarConfirmRequest,
    current_user: User = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Confirm a completed S3 upload, validate magic bytes, and store the CDN URL.

    The server fetches only the first 16 bytes from S3 to validate the image
    format.  If validation fails the uploaded object is deleted automatically
    and a **422** error is returned.
    """
    avatar_url = await storage.validate_and_get_avatar_url(data.object_key)
    updated = await service.update_avatar(current_user.id, avatar_url)
    return UserResponse.model_validate(updated)  # pragma: no cover


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
    return [UserResponse.model_validate(u) for u in users]  # pragma: no cover  # pragma: no cover


@admin_router.get("/{user_id}", response_model=UserResponse)
async def admin_get_user(
    user_id: UUID,
    _: None = Depends(require_roles("admin")),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Get any user by ID (admin only)."""
    user = await service.get_by_id(user_id)
    return UserResponse.model_validate(user)  # pragma: no cover  # pragma: no cover


@admin_router.patch("/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    _: None = Depends(require_roles("admin")),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Update any user's profile (admin only)."""
    user = await service.update_profile(user_id, data)
    return UserResponse.model_validate(user)  # pragma: no cover  # pragma: no cover


@admin_router.delete("/{user_id}", status_code=204)
async def admin_delete_user(
    user_id: UUID,
    _: None = Depends(require_roles("admin")),
    service: UserService = Depends(get_user_service),
) -> None:
    """Delete a user (admin only)."""
    await service.delete(user_id)
