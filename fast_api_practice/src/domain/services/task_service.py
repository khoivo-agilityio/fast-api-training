from datetime import datetime

from src.domain.entities.project_member import ProjectMemberRole
from src.domain.entities.task import TaskEntity, TaskPriority, TaskStatus
from src.domain.exceptions import AuthorizationError, NotFoundError
from src.domain.repositories.project_repository import ProjectRepository
from src.domain.repositories.task_repository import TaskRepository


class TaskService:
    def __init__(
        self,
        task_repo: TaskRepository,
        project_repo: ProjectRepository,
    ) -> None:
        self._tasks = task_repo
        self._projects = project_repo

    async def create_task(
        self,
        project_id: int,
        creator_id: int,
        title: str,
        description: str | None = None,
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        assignee_id: int | None = None,
        due_date: datetime | None = None,
    ) -> TaskEntity:
        await self._require_project_member(project_id, creator_id)

        if assignee_id is not None:
            await self._require_project_member(
                project_id, assignee_id, error_msg="Assignee is not a project member"
            )

        return await self._tasks.create(
            title=title,
            project_id=project_id,
            creator_id=creator_id,
            description=description,
            status=status,
            priority=priority,
            assignee_id=assignee_id,
            due_date=due_date,
        )

    async def get_task(
        self, task_id: int, requester_id: int, project_id: int | None = None
    ) -> TaskEntity:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        if project_id is not None and task.project_id != project_id:
            raise NotFoundError("Task not found")
        await self._require_project_member(task.project_id, requester_id)
        return task

    async def list_tasks(
        self,
        project_id: int,
        requester_id: int,
        *,
        task_status: TaskStatus | None = None,
        assignee_id: int | None = None,
        priority: TaskPriority | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[TaskEntity], int]:
        await self._require_project_member(project_id, requester_id)
        items = await self._tasks.list_for_project(
            project_id,
            status=task_status,
            assignee_id=assignee_id,
            priority=priority,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        total = await self._tasks.count_for_project(
            project_id,
            status=task_status,
            assignee_id=assignee_id,
            priority=priority,
        )
        return items, total

    async def update_task(
        self,
        task_id: int,
        requester_id: int,
        project_id: int | None = None,
        **fields: object,
    ) -> TaskEntity:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        if project_id is not None and task.project_id != project_id:
            raise NotFoundError("Task not found")
        await self._require_task_mutator(task, requester_id)

        new_assignee_id = fields.get("assignee_id")
        if new_assignee_id is not None:
            await self._require_project_member(
                task.project_id,
                int(new_assignee_id),  # type: ignore[arg-type]
                error_msg="Assignee is not a project member",
            )

        updated = await self._tasks.update(task_id, **fields)
        if updated is None:
            raise NotFoundError("Task not found")
        return updated

    async def delete_task(
        self, task_id: int, requester_id: int, project_id: int | None = None
    ) -> None:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        if project_id is not None and task.project_id != project_id:
            raise NotFoundError("Task not found")
        await self._require_task_deleter(task, requester_id)
        await self._tasks.delete(task_id)

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _require_project_member(
        self,
        project_id: int,
        user_id: int,
        error_msg: str = "You are not a member of this project",
    ) -> None:
        project = await self._projects.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")
        if project.owner_id == user_id:
            return
        member = await self._projects.get_member(project_id, user_id)
        if member is None:
            raise AuthorizationError(error_msg)

    async def _require_task_mutator(self, task: TaskEntity, user_id: int) -> None:
        """Creator, assignee, or project admin can update a task."""
        if task.creator_id == user_id:
            return
        if task.assignee_id is not None and task.assignee_id == user_id:
            return
        project = await self._projects.get_by_id(task.project_id)
        if project is not None and project.owner_id == user_id:
            return
        member = await self._projects.get_member(task.project_id, user_id)
        if member is not None and member.role == ProjectMemberRole.ADMIN:
            return
        raise AuthorizationError(
            "Only the task creator, assignee, or a project admin can update this task"
        )

    async def _require_task_deleter(self, task: TaskEntity, user_id: int) -> None:
        """Creator or project admin can delete a task."""
        if task.creator_id == user_id:
            return
        project = await self._projects.get_by_id(task.project_id)
        if project is not None and project.owner_id == user_id:
            return
        member = await self._projects.get_member(task.project_id, user_id)
        if member is not None and member.role == ProjectMemberRole.ADMIN:
            return
        raise AuthorizationError(
            "Only the task creator or a project admin can delete this task"
        )
