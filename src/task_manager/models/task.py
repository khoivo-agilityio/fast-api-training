from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import TaskStatus


class TaskBase(BaseModel):
    """
    Base model with common task attributes.

    This serves as the foundation for all task-related models,
    containing only the core business attributes.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,  # Auto-strip whitespace
        validate_assignment=True,  # Validate on attribute assignment
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Task title (required, 1-200 chars)",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Task description (optional, max 1000 chars)",
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls: type[Self], v: str) -> str:
        """Ensure title is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_strip_or_none(cls: type[Self], v: str | None) -> str | None:
        """Strip description or return None if empty"""
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class TaskCreate(TaskBase):
    """
    Model for creating a new task.

    Inherits title and description from TaskBase.
    Optionally accepts initial status (defaults to BACKLOG).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Implement user authentication",
                    "description": "Add JWT-based authentication system",
                },
                {"title": "Write unit tests", "description": None, "status": "todo"},
            ]
        }
    )

    status: TaskStatus = Field(
        default=TaskStatus.BACKLOG,
        description="Initial task status (defaults to BACKLOG)",
    )


class TaskUpdate(BaseModel):
    """
    Model for updating an existing task.

    All fields are optional - only provided fields will be updated.
    Uses None to indicate "no change" vs. explicitly setting to null.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "examples": [
                {"title": "Updated task title"},
                {"status": "in_progress"},
                {
                    "title": "New title",
                    "description": "Updated description",
                    "status": "done",
                },
            ]
        },
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="New task title (optional)",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="New task description (optional, use empty string to clear)",
    )
    status: TaskStatus | None = Field(
        default=None, description="New task status (optional)"
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls: type[Self], v: str | None) -> str | None:
        """Ensure title is not just whitespace if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty or whitespace")
        return v.strip() if v else None

    @field_validator("description")
    @classmethod
    def description_strip_or_none(cls: type[Self], v: str | None) -> str | None:
        """Strip description or return None if empty"""
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class TaskInDB(TaskBase):
    """
    Internal model representing a task as stored in the database.

    Includes all fields: ID, timestamps, and base attributes.
    This is used internally by the repository layer.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,  # Serialize enums as strings
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Complete project documentation",
                "description": "Write comprehensive docs for the task manager",
                "status": "backlog",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
            }
        },
    )

    id: int = Field(..., ge=1, description="Unique task identifier (auto-generated)")
    status: TaskStatus = Field(
        default=TaskStatus.BACKLOG, description="Current task status"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


class Task(TaskInDB):
    """
    Public task model for API responses.

    This is the model returned to users. It's identical to TaskInDB
    but separated for clarity and future extensibility.
    """

    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "title": "Complete project documentation",
                    "description": "Write comprehensive docs for the task manager",
                    "status": "backlog",
                    "created_at": "2024-01-15T10:30:00.000000",
                    "updated_at": "2024-01-15T10:30:00.000000",
                },
                {
                    "id": 2,
                    "title": "Implement user authentication",
                    "description": None,
                    "status": "in_progress",
                    "created_at": "2024-01-15T11:00:00.000000",
                    "updated_at": "2024-01-15T14:30:00.000000",
                },
            ]
        },
    )


class TaskStatusUpdate(BaseModel):
    """
    Model specifically for status transitions.

    Used when you only want to update the status field,
    ensuring proper validation of status transitions.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"status": "todo"},
                {"status": "in_progress"},
                {"status": "done"},
            ]
        }
    )

    status: TaskStatus = Field(..., description="New task status (required)")


# Type alias for convenience
TaskID = int
