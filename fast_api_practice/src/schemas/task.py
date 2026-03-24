from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.entities.task import TaskPriority, TaskStatus

# ── Request schemas ───────────────────────────────────────────────────────────


class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=5000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None


# ── Response schemas ──────────────────────────────────────────────────────────


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    project_id: int
    creator_id: int
    assignee_id: int | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False

    model_config = {"from_attributes": True}
