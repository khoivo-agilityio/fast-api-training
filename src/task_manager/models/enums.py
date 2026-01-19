from enum import Enum


class TaskStatus(str, Enum):
    """Enum representing the workflow states of a task."""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    DONE = "done"
