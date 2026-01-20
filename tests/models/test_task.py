import unittest
from datetime import datetime

from pydantic import ValidationError

from src.task_manager.models.enums import TaskStatus
from src.task_manager.models.task import Task


class TestTaskModel(unittest.TestCase):
    """Unit tests for Task model validation"""

    def test_title_cannot_be_empty(self) -> None:
        """Test that title cannot be empty string"""
        with self.assertRaises(ValidationError) as context:
            Task(id=1, title="", description="Test task")

        # Verify the error is related to title length
        errors = context.exception.errors()
        self.assertTrue(any(error["loc"] == ("title",) for error in errors))

    def test_title_cannot_be_missing(self) -> None:
        """Test that title is required"""
        with self.assertRaises(ValidationError) as context:
            Task(id=1, description="Test task")

        # Verify the error is related to missing title
        errors = context.exception.errors()
        self.assertTrue(any(error["loc"] == ("title",) for error in errors))

    def test_default_status_is_backlog(self) -> None:
        """Test that default status is BACKLOG when not specified"""
        task = Task(id=1, title="Test Task", description="Test description")

        self.assertEqual(task.status, TaskStatus.BACKLOG)

    def test_valid_task_creation(self) -> None:
        """Test that a valid task can be created successfully"""
        task = Task(
            id=1,
            title="Complete project documentation",
            description="Write comprehensive docs for the task manager",
            status=TaskStatus.IN_PROGRESS,
        )

        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Complete project documentation")
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsInstance(task.created_at, datetime)
        self.assertIsInstance(task.updated_at, datetime)

    def test_title_max_length(self) -> None:
        """Test that title cannot exceed 200 characters"""
        long_title = "x" * 201
        with self.assertRaises(ValidationError) as context:
            Task(id=1, title=long_title)

        errors = context.exception.errors()
        self.assertTrue(any(error["loc"] == ("title",) for error in errors))

    def test_id_must_be_positive(self) -> None:
        """Test that id must be >= 1"""
        with self.assertRaises(ValidationError) as context:
            Task(id=0, title="Test Task")

        errors = context.exception.errors()
        self.assertTrue(any(error["loc"] == ("id",) for error in errors))


if __name__ == "__main__":
    unittest.main()
