from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.comment import CommentEntity
from src.domain.entities.project import ProjectEntity
from src.domain.entities.project_member import ProjectMemberEntity, ProjectMemberRole
from src.domain.entities.task import TaskEntity, TaskPriority, TaskStatus
from src.domain.entities.user import UserEntity, UserRole
from src.domain.repositories.comment_repository import CommentRepository
from src.domain.repositories.project_repository import ProjectRepository
from src.domain.repositories.task_repository import TaskRepository
from src.domain.repositories.user_repository import UserRepository
from src.infrastructure.database.models import (
    CommentModel,
    ProjectMemberModel,
    ProjectModel,
    TaskModel,
    UserModel,
)


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


# ── Project repository ────────────────────────────────────────────────────────


class SQLAlchemyProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, m: ProjectModel) -> ProjectEntity:
        return ProjectEntity(
            id=m.id,
            name=m.name,
            description=m.description,
            owner_id=m.owner_id,
            created_at=_as_utc(m.created_at),
            updated_at=_as_utc(m.updated_at),
        )

    def _member_to_entity(self, m: ProjectMemberModel) -> ProjectMemberEntity:
        return ProjectMemberEntity(
            id=m.id,
            project_id=m.project_id,
            user_id=m.user_id,
            role=ProjectMemberRole(m.role),
            joined_at=_as_utc(m.joined_at),
        )

    async def create(
        self,
        name: str,
        owner_id: int,
        description: str | None = None,
    ) -> ProjectEntity:
        project = ProjectModel(name=name, owner_id=owner_id, description=description)
        self._session.add(project)
        await self._session.flush()
        await self._session.refresh(project)
        return self._to_entity(project)

    async def get_by_id(self, id: int) -> ProjectEntity | None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_for_user(self, user_id: int) -> list[ProjectEntity]:
        result = await self._session.execute(
            select(ProjectModel)
            .join(
                ProjectMemberModel,
                ProjectMemberModel.project_id == ProjectModel.id,
            )
            .where(ProjectMemberModel.user_id == user_id)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, id: int, **fields: object) -> ProjectEntity | None:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        for key, value in fields.items():
            setattr(model, key, value)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: int) -> bool:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    # ── Members ──────────────────────────────────────────────────────────────

    async def add_member(
        self,
        project_id: int,
        user_id: int,
        role: ProjectMemberRole = ProjectMemberRole.MEMBER,
    ) -> ProjectMemberEntity:
        member = ProjectMemberModel(
            project_id=project_id, user_id=user_id, role=role.value
        )
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return self._member_to_entity(member)

    async def get_member(
        self, project_id: int, user_id: int
    ) -> ProjectMemberEntity | None:
        result = await self._session.execute(
            select(ProjectMemberModel).where(
                ProjectMemberModel.project_id == project_id,
                ProjectMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._member_to_entity(model) if model else None

    async def list_members(self, project_id: int) -> list[ProjectMemberEntity]:
        result = await self._session.execute(
            select(ProjectMemberModel).where(
                ProjectMemberModel.project_id == project_id
            )
        )
        return [self._member_to_entity(m) for m in result.scalars().all()]

    async def update_member_role(
        self, project_id: int, user_id: int, role: ProjectMemberRole
    ) -> ProjectMemberEntity | None:
        result = await self._session.execute(
            select(ProjectMemberModel).where(
                ProjectMemberModel.project_id == project_id,
                ProjectMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.role = role.value
        await self._session.flush()
        await self._session.refresh(model)
        return self._member_to_entity(model)

    async def remove_member(self, project_id: int, user_id: int) -> bool:
        result = await self._session.execute(
            select(ProjectMemberModel).where(
                ProjectMemberModel.project_id == project_id,
                ProjectMemberModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True


# ── Task repository ───────────────────────────────────────────────────────────


class SQLAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, m: TaskModel) -> TaskEntity:
        return TaskEntity(
            id=m.id,
            title=m.title,
            description=m.description,
            status=TaskStatus(m.status),
            priority=TaskPriority(m.priority),
            project_id=m.project_id,
            creator_id=m.creator_id,
            assignee_id=m.assignee_id,
            due_date=_as_utc(m.due_date) if m.due_date else None,
            created_at=_as_utc(m.created_at),
            updated_at=_as_utc(m.updated_at),
        )

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
        task = TaskModel(
            title=title,
            project_id=project_id,
            creator_id=creator_id,
            description=description,
            status=status.value,
            priority=priority.value,
            assignee_id=assignee_id,
            due_date=due_date,
        )
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return self._to_entity(task)

    async def get_by_id(self, id: int) -> TaskEntity | None:
        result = await self._session.execute(
            select(TaskModel).where(TaskModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_for_project(
        self,
        project_id: int,
        *,
        status: TaskStatus | None = None,
        assignee_id: int | None = None,
    ) -> list[TaskEntity]:
        query = select(TaskModel).where(TaskModel.project_id == project_id)
        if status is not None:
            query = query.where(TaskModel.status == status.value)
        if assignee_id is not None:
            query = query.where(TaskModel.assignee_id == assignee_id)
        result = await self._session.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, id: int, **fields: object) -> TaskEntity | None:
        result = await self._session.execute(
            select(TaskModel).where(TaskModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        for key, value in fields.items():
            setattr(model, key, value)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: int) -> bool:
        result = await self._session.execute(
            select(TaskModel).where(TaskModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True


# ── Comment repository ────────────────────────────────────────────────────────


class SQLAlchemyCommentRepository(CommentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, m: CommentModel) -> CommentEntity:
        return CommentEntity(
            id=m.id,
            content=m.content,
            author_id=m.author_id,
            task_id=m.task_id,
            created_at=_as_utc(m.created_at),
            updated_at=_as_utc(m.updated_at),
        )

    async def create(self, content: str, author_id: int, task_id: int) -> CommentEntity:
        comment = CommentModel(content=content, author_id=author_id, task_id=task_id)
        self._session.add(comment)
        await self._session.flush()
        await self._session.refresh(comment)
        return self._to_entity(comment)

    async def get_by_id(self, id: int) -> CommentEntity | None:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.id == id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_for_task(self, task_id: int) -> list[CommentEntity]:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.task_id == task_id)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, id: int, content: str) -> CommentEntity | None:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.content = content
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_entity(model)

    async def delete(self, id: int) -> bool:
        result = await self._session.execute(
            select(CommentModel).where(CommentModel.id == id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
