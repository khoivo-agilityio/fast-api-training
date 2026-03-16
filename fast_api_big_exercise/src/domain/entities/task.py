"""Task domain entity - pure Python business object."""

from datetime import UTC, datetime

from src.schemas.task_schemas import TaskPriority, TaskStatus


class Task:
    """
    Task domain entity (pure Python, no database dependencies).

    Represents a task in the business domain.
    This is a rich domain model with business logic.
    """

    def __init__(
        self,
        title: str,
        owner_id: int,
        description: str | None = None,
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: datetime | None = None,
        id: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        """
        Initialize a Task entity.

        Args:
            title: Task title (1-200 chars)
            owner_id: ID of user who owns this task
            description: Task description (optional, max 1000 chars)
            status: Task status (default: TODO)
            priority: Task priority (default: MEDIUM)
            due_date: Task due date (optional)
            id: Task ID (None for new tasks)
            created_at: Creation timestamp (None = now)
            updated_at: Last update timestamp (None = now)
        """
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.owner_id = owner_id
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or datetime.now(UTC)
        self.due_date = due_date

    def mark_as_done(self) -> None:
        """
        Mark task as completed.

        Business rule: Completed tasks should have DONE status.
        """
        self.status = TaskStatus.DONE
        self.updated_at = datetime.now(UTC)

    def mark_as_in_progress(self) -> None:
        """
        Mark task as in progress.

        Business rule: Use this when starting work on a task.
        """
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now(UTC)

    def mark_as_todo(self) -> None:
        """
        Mark task as todo.

        Business rule: Use this to reset a task or move it back to backlog.
        """
        self.status = TaskStatus.TODO
        self.updated_at = datetime.now(UTC)

    def update_title(self, new_title: str) -> None:
        """
        Update task title.

        Args:
            new_title: New task title
        """
        self.title = new_title
        self.updated_at = datetime.now(UTC)

    def update_description(self, new_description: str | None) -> None:
        """
        Update task description.

        Args:
            new_description: New description (can be None to clear)
        """
        self.description = new_description
        self.updated_at = datetime.now(UTC)

    def update_priority(self, new_priority: TaskPriority) -> None:
        """
        Update task priority.

        Args:
            new_priority: New priority level
        """
        self.priority = new_priority
        self.updated_at = datetime.now(UTC)

    def update_due_date(self, new_due_date: datetime | None) -> None:
        """
        Update task due date.

        Args:
            new_due_date: New due date (can be None to clear)
        """
        self.due_date = new_due_date
        self.updated_at = datetime.now(UTC)

    def is_overdue(self) -> bool:
        """
        Check if task is overdue.

        Business rule: A task is overdue if:
        - It has a due date
        - Current time is past the due date
        - Task is not done

        Returns:
            bool: True if task is overdue
        """
        if not self.due_date:
            return False
        if self.status == TaskStatus.DONE:
            return False
        now = datetime.now(UTC)
        due = self.due_date if self.due_date.tzinfo else self.due_date.replace(tzinfo=UTC)
        return now > due

    def is_high_priority(self) -> bool:
        """
        Check if task has high priority.

        Returns:
            bool: True if task priority is HIGH
        """
        return self.priority == TaskPriority.HIGH

    def is_completed(self) -> bool:
        """
        Check if task is completed.

        Returns:
            bool: True if task status is DONE
        """
        return self.status == TaskStatus.DONE

    def days_until_due(self) -> int | None:
        """
        Calculate days until task is due.

        Returns:
            int | None: Number of days (negative if overdue), None if no due date
        """
        if not self.due_date:
            return None
        delta = self.due_date - datetime.now(UTC)
        return delta.days

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"<Task(id={self.id}, title='{self.title}', "
            f"status={self.status.value}, priority={self.priority.value})>"
        )

    def __eq__(self, other: object) -> bool:
        """
        Compare tasks by ID.

        Two tasks are equal if they have the same ID.
        """
        if not isinstance(other, Task):
            return False
        return self.id == other.id if self.id is not None else False

    def __hash__(self) -> int:
        """Hash task by ID for use in sets/dicts."""
        return hash(self.id) if self.id is not None else hash(id(self))
