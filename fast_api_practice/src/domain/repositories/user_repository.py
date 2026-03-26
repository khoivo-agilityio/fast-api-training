from abc import abstractmethod

from src.domain.entities.user import UserEntity
from src.domain.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """Abstract interface for user data access."""

    @abstractmethod
    async def create(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        role: str = "member",
    ) -> UserEntity:
        ...

    @abstractmethod
    async def get_by_id(self, id: int) -> UserEntity | None:
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> UserEntity | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> UserEntity | None:
        ...

    @abstractmethod
    async def update(self, id: int, **fields: object) -> UserEntity | None:
        ...

    @abstractmethod
    async def list_all(self, limit: int = 20, offset: int = 0) -> list[UserEntity]:
        ...

    @abstractmethod
    async def count_all(self) -> int:
        ...
