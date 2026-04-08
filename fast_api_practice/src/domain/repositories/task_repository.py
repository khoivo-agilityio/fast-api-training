from abc import abstractmethod

from src.domain.entities.task import TaskEntity, TaskPriority, TaskStatus
from src.domain.repositories.base import BaseRepository


class TaskRepository(BaseRepository):
    """Abstract interface for task data access."""

    @abstractmethod
    async def create(
        self,
        title: str,
        project_id: int,
        creator_id: int,
        description: str | None = None,
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee_id: int | None = None,
        due_date: object = None,
    ) -> TaskEntity:
        ...

    @abstractmethod
    async def get_by_id(self, id: int) -> TaskEntity | None:
        ...

    @abstractmethod
    async def list_for_project(
        self,
        project_id: int,
        *,
        status: TaskStatus | None = None,
        assignee_id: int | None = None,
        priority: TaskPriority | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> list[TaskEntity]:
        ...

    @abstractmethod
    async def count_for_project(
        self,
        project_id: int,
        *,
        status: TaskStatus | None = None,
        assignee_id: int | None = None,
        priority: TaskPriority | None = None,
    ) -> int:
        ...

    @abstractmethod
    async def update(self, id: int, **fields: object) -> TaskEntity | None:
        ...

    @abstractmethod
    async def delete(self, id: int) -> bool:
        ...
