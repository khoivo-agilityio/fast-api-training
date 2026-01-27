from enum import Enum
from typing import Self


class TaskStatus(str, Enum):
    """Enum representing the workflow states of a task."""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    DONE = "done"

    @classmethod
    def from_string(cls: type[Self], value: str) -> Self:
        """
        Parse a status string (case-insensitive, handles hyphens).

        Args:
            value: Status string (e.g., 'todo', 'in-progress', 'IN_PROGRESS')

        Returns:
            TaskStatus enum value

        Raises:
            ValueError: If status string is invalid
        """
        normalized = value.lower().replace("-", "_")
        try:
            return cls(normalized)
        except ValueError as exc:
            valid = [s.value for s in cls]
            message = f"Invalid status: '{value}'. Valid: {', '.join(valid)}"
            raise ValueError(message) from exc
