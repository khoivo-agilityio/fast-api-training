from fastapi import APIRouter, Depends, Query, status

from src.api.dependencies import get_current_user, get_task_service
from src.domain.entities.task import TaskEntity, TaskPriority, TaskStatus
from src.domain.entities.user import UserEntity
from src.domain.services.task_service import TaskService
from src.schemas.common import PaginatedResponse, PaginationParams
from src.schemas.task import TaskCreateRequest, TaskResponse, TaskUpdateRequest

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["Tasks"])


def _task_response(task: TaskEntity) -> TaskResponse:
    data = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "project_id": task.project_id,
        "creator_id": task.creator_id,
        "assignee_id": task.assignee_id,
        "due_date": task.due_date,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "is_overdue": task.is_overdue(),
    }
    return TaskResponse.model_validate(data)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    body: TaskCreateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.create_task(
        project_id=project_id,
        creator_id=current_user.id,
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        assignee_id=body.assignee_id,
        due_date=body.due_date,
    )
    return _task_response(task)


@router.get("", response_model=PaginatedResponse[TaskResponse])
async def list_tasks(
    project_id: int,
    task_status: TaskStatus | None = Query(None, alias="status"),
    assignee_id: int | None = Query(None),
    priority: TaskPriority | None = Query(None),
    sort_by: str = Query(
        "created_at", pattern="^(created_at|due_date|priority|title)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    pagination: PaginationParams = Depends(),
    current_user: UserEntity = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> PaginatedResponse[TaskResponse]:
    items, total = await service.list_tasks(
        project_id=project_id,
        requester_id=current_user.id,
        task_status=task_status,
        assignee_id=assignee_id,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return PaginatedResponse(
        items=[_task_response(t) for t in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    project_id: int,
    task_id: int,
    current_user: UserEntity = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.get_task(task_id, current_user.id)
    return _task_response(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    project_id: int,
    task_id: int,
    body: TaskUpdateRequest,
    current_user: UserEntity = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    updates = body.model_dump(exclude_unset=True)
    if "status" in updates and updates["status"] is not None:
        updates["status"] = updates["status"].value
    if "priority" in updates and updates["priority"] is not None:
        updates["priority"] = updates["priority"].value
    task = await service.update_task(
        task_id=task_id,
        requester_id=current_user.id,
        **updates,
    )
    return _task_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: int,
    task_id: int,
    current_user: UserEntity = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> None:
    await service.delete_task(task_id=task_id, requester_id=current_user.id)
