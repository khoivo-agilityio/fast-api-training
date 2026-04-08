from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class TaskEntity:
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

    def is_overdue(self) -> bool:
        if self.due_date is None or self.status == TaskStatus.DONE:
            return False
        now = datetime.now(UTC)
        due = (
            self.due_date if self.due_date.tzinfo else self.due_date.replace(tzinfo=UTC)
        )
        return now > due
