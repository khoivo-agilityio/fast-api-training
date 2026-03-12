"""Task repository interface (abstract base class).

This module defines the contract for task data access operations.
The actual implementation will be in the infrastructure layer.
"""

from abc import ABC, abstractmethod

from src.domain.entities.task import Task
from src.schemas.task_schemas import TaskStatus


class TaskRepository(ABC):
    """
    Abstract repository for Task entity.

    This is an INTERFACE - it defines the contract for task data access.
    Any class that implements this interface must provide all these methods.

    Benefits:
    - Separates domain logic from infrastructure concerns
    - Makes it easy to swap database implementations
    - Enables better testing with mock repositories
    - Follows Dependency Inversion Principle (SOLID)
    """

    @abstractmethod
    def create(self, task: Task) -> Task:
        """Create a new task.

        Args:
            task: Task entity to create

        Returns:
            Task: Created task with ID assigned
        """
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Task | None:
        """Get task by ID.

        Args:
            task_id: Task ID to search for

        Returns:
            Task | None: Task if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(
        self,
        owner_id: int,
        skip: int = 0,
        limit: int = 20,
        status: TaskStatus | None = None,
    ) -> list[Task]:
        """Get all tasks for a user with optional filters.

        Args:
            owner_id: ID of task owner
            skip: Number of tasks to skip (for pagination)
            limit: Maximum number of tasks to return
            status: Optional status filter (TODO, IN_PROGRESS, DONE)

        Returns:
            list[Task]: List of tasks matching criteria
        """
        pass

    @abstractmethod
    def count(self, owner_id: int, status: TaskStatus | None = None) -> int:
        """Count tasks for a user.

        Args:
            owner_id: ID of task owner
            status: Optional status filter

        Returns:
            int: Number of tasks matching criteria
        """
        pass

    @abstractmethod
    def update(self, task: Task) -> Task:
        """Update existing task.

        Args:
            task: Task entity with updated data

        Returns:
            Task: Updated task entity

        Raises:
            ValueError: If task not found
        """
        pass

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        """Delete task by ID.

        Args:
            task_id: ID of task to delete

        Returns:
            bool: True if deleted, False if not found
        """
        pass
