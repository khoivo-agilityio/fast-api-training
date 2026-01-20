from typing import Protocol

from ..models import Task


class TaskRepository(Protocol):
    """Repository interface for task storage abstraction"""

    def add(self, task: Task) -> Task:
        """
        Add a new task to the repository.

        Args:
            task: Task to add (ID will be auto-generated if not set)

        Returns:
            Task with assigned ID
        """
        ...

    def list(self) -> list[Task]:
        """
        Retrieve all tasks from the repository.

        Returns:
            List of all tasks
        """
        ...

    def get_by_id(self, task_id: int) -> Task | None:
        """
        Retrieve a task by its ID.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            Task if found, None otherwise
        """
        ...

    def update(self, task: Task) -> Task | None:
        """
        Update an existing task.

        Args:
            task: Task with updated fields

        Returns:
            Updated task if found, None otherwise
        """
        ...

    def delete(self, task_id: int) -> bool:
        """
        Delete a task by its ID.

        Args:
            task_id: The ID of the task to delete

        Returns:
            True if task was deleted, False if not found
        """
        ...
