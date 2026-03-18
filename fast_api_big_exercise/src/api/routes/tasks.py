"""Task CRUD routes."""

from fastapi import APIRouter, HTTPException, Query, status

from src.api.dependencies import CurrentUser, TaskServiceDep
from src.infrastructure.database.models import TaskStatus
from src.schemas.task_schemas import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    task_data: TaskCreate,
    task_service: TaskServiceDep,
    current_user: CurrentUser,
) -> TaskResponse:
    """
    Create a new task for the current user.

    - **title**: required, 1-200 characters
    - **description**: optional
    - **status**: todo | in_progress | done (default: todo)
    - **priority**: low | medium | high (default: medium)
    - **due_date**: optional ISO datetime
    """
    task = task_service.create_task(task_data, owner_id=current_user.id)
    return TaskResponse.model_validate(task.__dict__)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks with pagination",
)
def list_tasks(
    task_service: TaskServiceDep,
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: TaskStatus | None = Query(default=None, description="Filter by status"),
) -> TaskListResponse:
    """
    List tasks for the current user with pagination and optional status filter.
    """
    return task_service.list_tasks(
        owner_id=current_user.id,
        page=page,
        size=size,
        status=status,
    )


@router.get(
    "/stats",
    response_model=TaskStatsResponse,
    summary="Get task statistics",
)
def get_stats(
    task_service: TaskServiceDep,
    current_user: CurrentUser,
) -> TaskStatsResponse:
    """
    Get task statistics for the current user:
    counts by status, priority, and number of overdue tasks.
    """
    return task_service.get_stats(owner_id=current_user.id)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task",
)
def get_task(
    task_id: int,
    task_service: TaskServiceDep,
    current_user: CurrentUser,
) -> TaskResponse:
    """Get a single task by ID. Only the task owner can access it."""
    try:
        task = task_service.get_task(task_id, owner_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return TaskResponse.model_validate(task.__dict__)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    task_service: TaskServiceDep,
    current_user: CurrentUser,
) -> TaskResponse:
    """
    Update a task's fields. Only provided fields are updated.
    Only the task owner can update it.
    """
    try:
        task = task_service.update_task(task_id, task_data, owner_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return TaskResponse.model_validate(task.__dict__)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(
    task_id: int,
    task_service: TaskServiceDep,
    current_user: CurrentUser,
) -> None:
    """Delete a task by ID. Only the task owner can delete it."""
    try:
        task_service.delete_task(task_id, owner_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
