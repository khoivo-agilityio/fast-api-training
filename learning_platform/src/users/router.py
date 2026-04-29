"""User router — GET /users/me, PATCH /users/me."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import CurrentUser
from src.database import get_db
from src.users import service as user_service
from src.users.schemas import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile.",
)
async def get_me(
    payload: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await user_service.get_me(session, uuid.UUID(payload["sub"]))
    return UserResponse.model_validate(user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update display_name, avatar, or password for the authenticated user.",
)
async def update_me(
    data: UserUpdateRequest,
    payload: CurrentUser,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await user_service.update_me(session, uuid.UUID(payload["sub"]), data)
    return UserResponse.model_validate(user)
