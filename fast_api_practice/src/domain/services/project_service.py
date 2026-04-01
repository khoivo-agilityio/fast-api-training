from src.domain.entities.project import ProjectEntity
from src.domain.entities.project_member import ProjectMemberEntity, ProjectMemberRole
from src.domain.repositories.project_repository import ProjectRepository
from src.domain.repositories.user_repository import UserRepository


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        user_repo: UserRepository,
    ) -> None:
        self._projects = project_repo
        self._users = user_repo

    async def create_project(
        self,
        name: str,
        owner_id: int,
        description: str | None = None,
    ) -> ProjectEntity:
        project = await self._projects.create(
            name=name, owner_id=owner_id, description=description
        )
        # Auto-add owner as admin member
        await self._projects.add_member(
            project_id=project.id,
            user_id=owner_id,
            role=ProjectMemberRole.ADMIN,
        )
        return project

    async def get_project(self, project_id: int) -> ProjectEntity:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise LookupError("Project not found")
        return project

    async def list_projects(
        self, user_id: int, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[ProjectEntity], int]:
        items = await self._projects.list_for_user(user_id, limit=limit, offset=offset)
        total = await self._projects.count_for_user(user_id)
        return items, total

    async def update_project(
        self,
        project_id: int,
        requester_id: int,
        **fields: object,
    ) -> ProjectEntity:
        project = await self.get_project(project_id)
        await self._require_project_admin(project, requester_id)
        updated = await self._projects.update(project_id, **fields)
        if updated is None:
            raise LookupError("Project not found")
        return updated

    async def delete_project(self, project_id: int, requester_id: int) -> None:
        project = await self.get_project(project_id)
        await self._require_project_admin(project, requester_id)
        await self._projects.delete(project_id)

    # ── Members ──────────────────────────────────────────────────────────────

    async def add_member(
        self,
        project_id: int,
        requester_id: int,
        user_id: int,
        role: ProjectMemberRole = ProjectMemberRole.MEMBER,
    ) -> ProjectMemberEntity:
        project = await self.get_project(project_id)
        await self._require_project_admin(project, requester_id)

        target_user = await self._users.get_by_id(user_id)
        if target_user is None:
            raise LookupError("User not found")

        existing = await self._projects.get_member(project_id, user_id)
        if existing is not None:
            raise ValueError("User is already a member of this project")

        return await self._projects.add_member(
            project_id=project_id, user_id=user_id, role=role
        )

    async def list_members(self, project_id: int) -> list[ProjectMemberEntity]:
        await self.get_project(project_id)
        return await self._projects.list_members(project_id)

    async def update_member_role(
        self,
        project_id: int,
        requester_id: int,
        user_id: int,
        role: ProjectMemberRole,
    ) -> ProjectMemberEntity:
        project = await self.get_project(project_id)
        await self._require_project_admin(project, requester_id)

        if user_id == project.owner_id:
            raise PermissionError("Cannot change role of project owner")

        updated = await self._projects.update_member_role(project_id, user_id, role)
        if updated is None:
            raise LookupError("Member not found in this project")
        return updated

    async def remove_member(
        self, project_id: int, requester_id: int, user_id: int
    ) -> None:
        project = await self.get_project(project_id)
        await self._require_project_admin(project, requester_id)

        if user_id == project.owner_id:
            raise PermissionError("Cannot remove the project owner")

        removed = await self._projects.remove_member(project_id, user_id)
        if not removed:
            raise LookupError("Member not found in this project")

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _require_project_admin(
        self, project: ProjectEntity, user_id: int
    ) -> None:
        """Raise PermissionError unless user is owner or project admin."""
        if project.owner_id == user_id:
            return
        member = await self._projects.get_member(project.id, user_id)
        if member is None or member.role != ProjectMemberRole.ADMIN:
            raise PermissionError("You do not have admin access to this project")
