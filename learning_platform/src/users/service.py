"""User business logic — profile get/update.

No repository layer: this service queries the DB directly via AsyncSession.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import hash_password
from src.users.exceptions import UserNotFound
from src.users.models import User
from src.users.schemas import UserUpdateRequest


async def get_me(session: AsyncSession, user_id: uuid.UUID) -> User:
    """Fetch the current user by ID."""
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFound()
    return user


async def update_me(session: AsyncSession, user_id: uuid.UUID, data: UserUpdateRequest) -> User:
    """Update the current user's profile fields."""
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFound()

    if data.display_name is not None:
        user.display_name = data.display_name
    if data.avatar is not None:
        user.avatar = data.avatar
    if data.password is not None:
        user.password = hash_password(data.password)

    await session.commit()
    await session.refresh(user)
    return user
