"""Task service - business logic for task management."""

from math import ceil

from src.domain.entities.task import Task
from src.domain.repositories.task_repository import TaskRepository
from src.schemas.task_schemas import (
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStatsResponse,
    TaskStatus,
    TaskUpdate,
)


class TaskService:
    """
    Task service.

    Handles: create, read, update, delete, list, statistics.

    Depends on TaskRepository interface — NOT the database directly.
    All authorization checks (ownership) happen here, not in the routes.
    """

    def __init__(self, task_repository: TaskRepository) -> None:
        self.task_repository = task_repository

    def create_task(self, task_data: TaskCreate, owner_id: int) -> Task:
        """
        Create a new task for a user.

        Args:
            task_data: Validated task creation data
            owner_id: ID of the user creating the task

        Returns:
            Task: Created task entity
        """
        task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            owner_id=owner_id,
            due_date=task_data.due_date,
        )
        return self.task_repository.create(task)

    def get_task(self, task_id: int, owner_id: int) -> Task:
        """
        Get task by ID with ownership check.

        Args:
            task_id: Task ID to retrieve
            owner_id: ID of the requesting user

        Returns:
            Task: Task entity

        Raises:
            ValueError: If task not found
            PermissionError: If task belongs to another user
        """
        task = self.task_repository.get_by_id(task_id)

        if not task:
            raise ValueError(f"Task {task_id} not found")
        if task.owner_id != owner_id:
            raise PermissionError("Not authorized to access this task")

        return task

    def list_tasks(
        self,
        owner_id: int,
        page: int = 1,
        size: int = 20,
        status: TaskStatus | None = None,
    ) -> TaskListResponse:
        """
        List tasks with pagination and optional status filter.

        Args:
            owner_id: ID of the task owner
            page: Page number (starts at 1)
            size: Items per page
            status: Optional filter by status

        Returns:
            TaskListResponse: Paginated task list with metadata
        """
        skip = (page - 1) * size
        tasks = self.task_repository.get_all(owner_id, skip=skip, limit=size, status=status)
        total = self.task_repository.count(owner_id, status=status)
        pages = ceil(total / size) if size > 0 else 0

        return TaskListResponse(
            items=[TaskResponse.model_validate(t.__dict__) for t in tasks],
            total=total,
            page=page,
            size=len(tasks),
            pages=pages,
        )

    def update_task(self, task_id: int, task_data: TaskUpdate, owner_id: int) -> Task:
        """
        Update task fields with ownership check.

        Only updates fields that are explicitly provided (not None).

        Args:
            task_id: Task ID to update
            task_data: Fields to update (all optional)
            owner_id: ID of the requesting user

        Returns:
            Task: Updated task entity

        Raises:
            ValueError: If task not found
            PermissionError: If task belongs to another user
        """
        # get_task validates ownership
        task = self.get_task(task_id, owner_id)

        # Only update fields that were explicitly provided
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.status is not None:
            task.status = task_data.status
        if task_data.priority is not None:
            task.priority = task_data.priority
        if task_data.due_date is not None:
            task.due_date = task_data.due_date

        return self.task_repository.update(task)

    def delete_task(self, task_id: int, owner_id: int) -> bool:
        """
        Delete task with ownership check.

        Args:
            task_id: Task ID to delete
            owner_id: ID of the requesting user

        Returns:
            bool: True if deleted

        Raises:
            ValueError: If task not found
            PermissionError: If task belongs to another user
        """
        # get_task validates ownership
        self.get_task(task_id, owner_id)
        return self.task_repository.delete(task_id)

    def get_stats(self, owner_id: int) -> TaskStatsResponse:
        """
        Get task statistics for a user.

        Args:
            owner_id: ID of the task owner

        Returns:
            TaskStatsResponse: Counts by status, priority, and overdue
        """
        total = self.task_repository.count(owner_id)
        todo = self.task_repository.count(owner_id, TaskStatus.TODO)
        in_progress = self.task_repository.count(owner_id, TaskStatus.IN_PROGRESS)
        done = self.task_repository.count(owner_id, TaskStatus.DONE)

        # Fetch all tasks to calculate overdue and priority counts
        all_tasks = self.task_repository.get_all(owner_id, skip=0, limit=max(total, 1))
        overdue = sum(1 for t in all_tasks if t.is_overdue())
        by_priority = {
            TaskPriority.LOW.value: sum(1 for t in all_tasks if t.priority == TaskPriority.LOW),
            TaskPriority.MEDIUM.value: sum(
                1 for t in all_tasks if t.priority == TaskPriority.MEDIUM
            ),
            TaskPriority.HIGH.value: sum(1 for t in all_tasks if t.priority == TaskPriority.HIGH),
        }

        return TaskStatsResponse(
            total=total,
            todo=todo,
            in_progress=in_progress,
            done=done,
            by_priority=by_priority,
            overdue=overdue,
        )
