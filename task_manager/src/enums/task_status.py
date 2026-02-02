from __future__ import annotations

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

    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """
        Check if transition to new_status is valid.

        Args:
            new_status: Target status to transition to

        Returns:
            True if transition is valid, False otherwise

        Examples:
            >>> TaskStatus.BACKLOG.can_transition_to(TaskStatus.TODO)
            True
            >>> TaskStatus.BACKLOG.can_transition_to(TaskStatus.DONE)
            False
            >>> TaskStatus.DONE.can_transition_to(TaskStatus.TODO)
            False
        """
        # Same status is always valid (no-op)
        if self == new_status:
            return True

        # Get valid next statuses for current status
        valid_transitions = self.get_valid_transitions()
        return new_status in valid_transitions

    def get_valid_transitions(self) -> list[TaskStatus]:
        """
        Get list of valid status transitions from current status.

        Returns:
            List of TaskStatus values that can be transitioned to

        Examples:
            >>> TaskStatus.BACKLOG.get_valid_transitions()
            [<TaskStatus.TODO: 'todo'>, <TaskStatus.IN_PROGRESS: 'in_progress'>]
            >>> TaskStatus.DONE.get_valid_transitions()
            []
        """
        transitions = {
            TaskStatus.BACKLOG: [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
            TaskStatus.TODO: [TaskStatus.BACKLOG, TaskStatus.IN_PROGRESS],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.TODO,
                TaskStatus.TESTING,
                TaskStatus.DONE,
            ],
            TaskStatus.TESTING: [TaskStatus.IN_PROGRESS, TaskStatus.DONE],
            TaskStatus.DONE: [],  # Cannot transition from DONE
        }
        return transitions.get(self, [])

    def get_transition_error_message(self, new_status: TaskStatus) -> str:
        """
        Get a user-friendly error message for invalid transition.

        Args:
            new_status: The status that was attempted to transition to

        Returns:
            Formatted error message explaining the invalid transition

        Examples:
            >>> TaskStatus.BACKLOG.get_transition_error_message(TaskStatus.DONE)
            "Invalid status transition from 'backlog' to 'done'. "
            "Valid transitions: todo, in_progress"
        """
        valid_transitions = self.get_valid_transitions()

        if not valid_transitions:
            return (
                f"Cannot transition from '{self.value}' (final state). "
                f"Task is already complete."
            )

        valid_transitions_str = ", ".join(s.value for s in valid_transitions)
        return (
            f"Invalid status transition from '{self.value}' to '{new_status.value}'. "
            f"Valid transitions: {valid_transitions_str}"
        )

    @property
    def is_final(self) -> bool:
        """
        Check if this is a final status (no further transitions).

        Returns:
            True if status is final (DONE), False otherwise
        """
        return self == TaskStatus.DONE

    @property
    def is_active(self) -> bool:
        """
        Check if this is an active work status.

        Returns:
            True if status is TODO, IN_PROGRESS, or TESTING
        """
        return self in (TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.TESTING)

    @property
    def is_pending(self) -> bool:
        """
        Check if this is a pending status (not started).

        Returns:
            True if status is BACKLOG or TODO
        """
        return self in (TaskStatus.BACKLOG, TaskStatus.TODO)
