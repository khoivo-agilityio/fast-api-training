from datetime import datetime

from fastapi import HTTPException, status

from src.domain.entities.task import TaskEntity, TaskPriority, TaskStatus
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

    async def get_task(self, task_id: int, requester_id: int) -> TaskEntity:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        await self._require_project_member(task.project_id, requester_id)
        return task

    async def list_tasks(
        self,
        project_id: int,
        requester_id: int,
        *,
        task_status: TaskStatus | None = None,
        assignee_id: int | None = None,
    ) -> list[TaskEntity]:
        await self._require_project_member(project_id, requester_id)
        return await self._tasks.list_for_project(
            project_id, status=task_status, assignee_id=assignee_id
        )

    async def update_task(
        self,
        task_id: int,
        requester_id: int,
        **fields: object,
    ) -> TaskEntity:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        await self._require_project_member(task.project_id, requester_id)

        new_assignee_id = fields.get("assignee_id")
        if new_assignee_id is not None:
            await self._require_project_member(
                task.project_id,
                int(new_assignee_id),  # type: ignore[arg-type]
                error_msg="Assignee is not a project member",
            )

        updated = await self._tasks.update(task_id, **fields)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        return updated

    async def delete_task(self, task_id: int, requester_id: int) -> None:
        task = await self._tasks.get_by_id(task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        await self._require_project_member(task.project_id, requester_id)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
            )
        if project.owner_id == user_id:
            return
        member = await self._projects.get_member(project_id, user_id)
        if member is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_msg)
