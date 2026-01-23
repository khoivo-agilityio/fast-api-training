"""Unit tests for Task model validation"""

import unittest
from datetime import datetime
from typing import Unpack

from pydantic import ValidationError

from src.task_manager.models.enums import TaskStatus
from src.task_manager.models.task import Task


class TestTaskModel(unittest.TestCase):
    """Unit tests for Task model validation"""

    # ========================================================================
    # HELPER METHODS - DRY PRINCIPLE
    # ========================================================================

    def assert_validation_error(
        self, error_field: str, **task_kwargs: Unpack[dict[str, object]]
    ) -> None:
        """
        Assert that creating a Task raises ValidationError for a specific field.

        Args:
            error_field: Field name that should have validation error
            **task_kwargs: Keyword arguments to pass to Task constructor
        """
        with self.assertRaises(ValidationError) as context:
            Task(**task_kwargs)

        errors = context.exception.errors()
        self.assertTrue(
            any(error["loc"] == (error_field,) for error in errors),
            f"Expected validation error for field '{error_field}', "
            f"but got errors: {errors}",
        )

    def create_valid_task(
        self,
        task_id: int = 1,
        title: str = "Test Task",
        description: str | None = "Test description",
        status: TaskStatus = TaskStatus.BACKLOG,
    ) -> Task:
        """
        Create a valid task with default or custom values.

        Args:
            task_id: Task ID (default: 1)
            title: Task title (default: "Test Task")
            description: Task description (default: "Test description")
            status: Task status (default: BACKLOG)

        Returns:
            Created Task instance
        """
        return Task(id=task_id, title=title, description=description, status=status)

    # ========================================================================
    # TEST CASES - TITLE VALIDATION
    # ========================================================================

    def test_title_cannot_be_empty(self) -> None:
        """Test that title cannot be empty string"""
        self.assert_validation_error("title", id=1, title="", description="Test task")

    def test_title_cannot_be_missing(self) -> None:
        """Test that title is required"""
        self.assert_validation_error("title", id=1, description="Test task")

    def test_title_max_length(self) -> None:
        """Test that title cannot exceed 200 characters"""
        long_title = "x" * 201
        self.assert_validation_error("title", id=1, title=long_title)

    # ========================================================================
    # TEST CASES - ID VALIDATION
    # ========================================================================

    def test_id_must_be_positive(self) -> None:
        """Test that id must be >= 1"""
        self.assert_validation_error("id", id=0, title="Test Task")

    # ========================================================================
    # TEST CASES - TASK CREATION
    # ========================================================================

    def test_default_status_is_backlog(self) -> None:
        """Test that default status is BACKLOG when not specified"""
        task = self.create_valid_task()
        self.assertEqual(task.status, TaskStatus.BACKLOG)

    def test_valid_task_creation(self) -> None:
        """Test that a valid task can be created successfully"""
        task = self.create_valid_task(
            task_id=1,
            title="Complete project documentation",
            description="Write comprehensive docs for the task manager",
            status=TaskStatus.IN_PROGRESS,
        )

        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Complete project documentation")
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsInstance(task.created_at, datetime)
        self.assertIsInstance(task.updated_at, datetime)

    def test_task_with_no_description(self) -> None:
        """Test that description is optional"""
        task = self.create_valid_task(description=None)
        self.assertIsNone(task.description)
        self.assertEqual(task.title, "Test Task")

    def test_timestamps_are_set(self) -> None:
        """Test that created_at and updated_at are automatically set"""
        task = self.create_valid_task()
        self.assertIsInstance(task.created_at, datetime)
        self.assertIsInstance(task.updated_at, datetime)
        self.assertEqual(task.created_at, task.updated_at)

    # ========================================================================
    # TEST CASES - TASK STATUS
    # ========================================================================

    def test_all_status_values_accepted(self) -> None:
        """Test that all TaskStatus enum values are valid"""
        for status in TaskStatus:
            task = self.create_valid_task(status=status)
            self.assertEqual(task.status, status)


if __name__ == "__main__":
    unittest.main()
