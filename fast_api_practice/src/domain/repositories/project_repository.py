from abc import abstractmethod

from src.domain.entities.project import ProjectEntity
from src.domain.entities.project_member import ProjectMemberEntity, ProjectMemberRole
from src.domain.repositories.base import BaseRepository


class ProjectRepository(BaseRepository):
    """Abstract interface for project data access."""

    @abstractmethod
    async def create(
        self,
        name: str,
        owner_id: int,
        description: str | None = None,
    ) -> ProjectEntity:
        ...

    @abstractmethod
    async def get_by_id(self, id: int) -> ProjectEntity | None:
        ...

    @abstractmethod
    async def list_for_user(
        self, user_id: int, *, limit: int = 20, offset: int = 0
    ) -> list[ProjectEntity]:
        ...

    @abstractmethod
    async def count_for_user(self, user_id: int) -> int:
        ...

    @abstractmethod
    async def update(self, id: int, **fields: object) -> ProjectEntity | None:
        ...

    @abstractmethod
    async def delete(self, id: int) -> bool:
        ...

    # ── Members ──────────────────────────────────────────────────────────────

    @abstractmethod
    async def add_member(
        self,
        project_id: int,
        user_id: int,
        role: ProjectMemberRole = ProjectMemberRole.MEMBER,
    ) -> ProjectMemberEntity:
        ...

    @abstractmethod
    async def get_member(
        self, project_id: int, user_id: int
    ) -> ProjectMemberEntity | None:
        ...

    @abstractmethod
    async def list_members(self, project_id: int) -> list[ProjectMemberEntity]:
        ...

    @abstractmethod
    async def update_member_role(
        self, project_id: int, user_id: int, role: ProjectMemberRole
    ) -> ProjectMemberEntity | None:
        ...

    @abstractmethod
    async def remove_member(self, project_id: int, user_id: int) -> bool:
        ...
