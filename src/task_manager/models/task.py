from datetime import datetime

from pydantic import BaseModel, Field

from .enums import TaskStatus


class Task(BaseModel):
    id: int = Field(..., ge=1, description="Unique task identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: str | None = Field(
        None, max_length=1000, description="Task description"
    )
    status: TaskStatus = Field(
        default=TaskStatus.BACKLOG, description="Current task status"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Complete project documentation",
                "description": "Write comprehensive docs for the task manager",
                "status": "backlog",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00",
            }
        }
