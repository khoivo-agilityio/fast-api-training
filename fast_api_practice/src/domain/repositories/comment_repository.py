from abc import abstractmethod

from src.domain.entities.comment import CommentEntity
from src.domain.repositories.base import BaseRepository


class CommentRepository(BaseRepository):
    """Abstract interface for comment data access."""

    @abstractmethod
    async def create(
        self,
        content: str,
        author_id: int,
        task_id: int,
    ) -> CommentEntity:
        ...

    @abstractmethod
    async def get_by_id(self, id: int) -> CommentEntity | None:
        ...

    @abstractmethod
    async def list_for_task(self, task_id: int) -> list[CommentEntity]:
        ...

    @abstractmethod
    async def update(self, id: int, content: str) -> CommentEntity | None:
        ...

    @abstractmethod
    async def delete(self, id: int) -> bool:
        ...
