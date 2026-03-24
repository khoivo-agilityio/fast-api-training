from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import UserEntity, UserRole
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.database.models import UserModel


def _as_utc(dt: datetime) -> datetime:
    """Ensure datetime is UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: UserModel) -> UserEntity:
        return UserEntity(
            id=model.id,
            username=model.username,
            email=model.email,
            hashed_password=model.hashed_password,
            full_name=model.full_name,
            is_active=model.is_active,
            role=UserRole(model.role),
            created_at=_as_utc(model.created_at),
            updated_at=_as_utc(model.updated_at),
        )

    async def create(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        role: str = "member",
    ) -> UserEntity:
        user = UserModel(
            username=username,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return self._to_entity(user)

    async def get_by_id(self, id: int) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: str) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def update(self, id: int, **fields: object) -> UserEntity | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        for key, value in fields.items():
            setattr(model, key, value)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)
