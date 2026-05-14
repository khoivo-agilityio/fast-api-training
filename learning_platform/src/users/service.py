"""
User Service — Profile Management.

Class-based service pattern (per code review feedback, Issue #4):
- Takes AsyncSession via constructor
- All DB queries are owned by this service (no repositories layer)
- Raises domain exceptions — never HTTPException
- Cross-module access goes through service public methods only
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import security
from src.users.exceptions import UserNotFound
from src.users.models import User
from src.users.schemas import UserUpdateRequest


class UserService:
    """Handles user profile CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: UUID) -> User:
        """Get user by ID or raise UserNotFound."""
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFound(user_id)
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email (returns None if not found — used by auth login)."""
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        display_name: str = "",
        role: str = "student",
    ) -> User:
        """Create a new user with a hashed password."""
        hashed = await security.hash_password(password)
        user = User(
            email=email,
            password=hashed,
            display_name=display_name,
            role=role,
        )
        self._db.add(user)
        await self._db.flush()
        return user

    async def update_profile(self, user_id: UUID, data: UserUpdateRequest) -> User:
        """Update user profile fields (partial update — only set fields are changed)."""
        user = await self.get_by_id(user_id)
        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("id", None)

        # If password is being updated, hash the new password
        if "password" in update_data:
            update_data["password"] = await security.hash_password(update_data["password"])

        for field, value in update_data.items():
            setattr(user, field, value)

        await self._db.flush()
        return user

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[User]:
        """List all users with pagination (admin use)."""
        result = await self._db.execute(
            select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def delete(self, user_id: UUID) -> None:
        """Delete a user by ID (admin use)."""
        user = await self.get_by_id(user_id)
        await self._db.delete(user)
        await self._db.flush()

    async def update_avatar(self, user_id: UUID, avatar_url: str) -> User:
        """Store a new avatar URL on the user record.

        Args:
            user_id: Target user.
            avatar_url: Fully-qualified CDN or MinIO URL for the uploaded image.
        """
        user = await self.get_by_id(user_id)
        user.avatar = avatar_url
        await self._db.flush()
        return user
