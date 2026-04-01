from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.entities.task import TaskPriority, TaskStatus

# ── Request schemas ───────────────────────────────────────────────────────────


class TaskCreateRequest(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, examples=["Implement login page"]
    )
    description: str | None = Field(
        None,
        max_length=5000,
        examples=["Build the login UI with email/password validation"],
    )
    status: TaskStatus = Field(TaskStatus.TODO, examples=["todo"])
    priority: TaskPriority = Field(TaskPriority.MEDIUM, examples=["medium"])
    assignee_id: int | None = Field(None, examples=[42])
    due_date: datetime | None = Field(None, examples=["2025-12-31T23:59:59Z"])


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(
        None, min_length=1, max_length=200, examples=["Updated task title"]
    )
    description: str | None = Field(None, examples=["Revised description"])
    status: TaskStatus | None = Field(None, examples=["in_progress"])
    priority: TaskPriority | None = Field(None, examples=["high"])
    assignee_id: int | None = Field(None, examples=[42])
    due_date: datetime | None = Field(None, examples=["2025-12-31T23:59:59Z"])


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
