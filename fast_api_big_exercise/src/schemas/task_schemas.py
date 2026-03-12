"""Task Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    """Task status enumeration."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(StrEnum):
    """Task priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskBase(BaseModel):
    """Base task schema with common fields."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task title (1-200 characters)",
        examples=["Complete project documentation"],
    )
    description: str | None = Field(
        None,
        max_length=1000,
        description="Task description (optional, max 1000 characters)",
        examples=["Write comprehensive API documentation with examples"],
    )
    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="Task status",
        examples=[TaskStatus.TODO],
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Task priority",
        examples=[TaskPriority.MEDIUM],
    )
    due_date: datetime | None = Field(
        None,
        description="Task due date (optional)",
        examples=["2026-03-20T10:00:00"],
    )


class TaskCreate(TaskBase):
    """Schema for task creation request."""

    pass


class TaskUpdate(BaseModel):
    """Schema for task update request (all fields optional)."""

    title: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="New task title",
    )
    description: str | None = Field(
        None,
        max_length=1000,
        description="New task description",
    )
    status: TaskStatus | None = Field(
        None,
        description="New task status",
    )
    priority: TaskPriority | None = Field(
        None,
        description="New task priority",
    )
    due_date: datetime | None = Field(
        None,
        description="New due date",
    )


class TaskResponse(TaskBase):
    """Schema for task response (returned to client)."""

    id: int = Field(..., description="Task ID", examples=[1])
    owner_id: int = Field(..., description="User ID of task owner", examples=[1])
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""

    items: list[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks", examples=[42])
    page: int = Field(..., description="Current page number", examples=[1])
    size: int = Field(..., description="Number of items in current page", examples=[20])
    pages: int = Field(..., description="Total number of pages", examples=[3])


class TaskStatsResponse(BaseModel):
    """Schema for task statistics response."""

    total: int = Field(..., description="Total number of tasks", examples=[42])
    todo: int = Field(..., description="Number of TODO tasks", examples=[15])
    in_progress: int = Field(..., description="Number of IN_PROGRESS tasks", examples=[10])
    done: int = Field(..., description="Number of DONE tasks", examples=[17])
    by_priority: dict[str, int] = Field(
        ...,
        description="Task count by priority",
        examples=[{"low": 10, "medium": 20, "high": 12}],
    )
    overdue: int = Field(..., description="Number of overdue tasks", examples=[5])
