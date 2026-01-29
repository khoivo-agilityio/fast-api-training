"""Unit tests for task model hierarchy"""

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from src.task_manager.enums import TaskStatus
from src.task_manager.models import (
    Task,
    TaskBase,
    TaskCreate,
    TaskUpdate,
)


class TestTaskBase(unittest.TestCase):
    """Tests for TaskBase model"""

    def test_valid_task_base(self) -> None:
        """Test creating valid TaskBase"""
        task_base = TaskBase(title="Test Task", description="Test Description")

        self.assertEqual(task_base.title, "Test Task")
        self.assertEqual(task_base.description, "Test Description")

    def test_title_required(self) -> None:
        """Test that title is required"""
        with self.assertRaises(ValidationError):
            TaskBase(description="Test")

    def test_title_empty_fails(self) -> None:
        """Test that empty title fails validation"""
        with self.assertRaises(ValidationError):
            TaskBase(title="", description="Test")

    def test_title_whitespace_only_fails(self) -> None:
        """Test that whitespace-only title fails"""
        with self.assertRaises(ValidationError):
            TaskBase(title="   ", description="Test")

    def test_title_strips_whitespace(self) -> None:
        """Test that title whitespace is stripped"""
        task_base = TaskBase(title="  Test Task  ")
        self.assertEqual(task_base.title, "Test Task")

    def test_description_optional(self) -> None:
        """Test that description is optional"""
        task_base = TaskBase(title="Test Task")
        self.assertIsNone(task_base.description)

    def test_description_strips_whitespace(self) -> None:
        """Test that description whitespace is stripped"""
        task_base = TaskBase(title="Test", description="  Description  ")
        self.assertEqual(task_base.description, "Description")

    def test_description_empty_becomes_none(self) -> None:
        """Test that empty description becomes None"""
        task_base = TaskBase(title="Test", description="   ")
        self.assertIsNone(task_base.description)


class TestTaskCreate(unittest.TestCase):
    """Tests for TaskCreate model"""

    def test_valid_task_create(self) -> None:
        """Test creating valid TaskCreate"""
        task_create = TaskCreate(title="New Task", description="Task description")

        self.assertEqual(task_create.title, "New Task")
        self.assertEqual(task_create.description, "Task description")
        self.assertEqual(task_create.status, TaskStatus.BACKLOG)

    def test_default_status_is_backlog(self) -> None:
        """Test that default status is BACKLOG"""
        task_create = TaskCreate(title="Test")
        self.assertEqual(task_create.status, TaskStatus.BACKLOG)

    def test_custom_initial_status(self) -> None:
        """Test setting custom initial status"""
        task_create = TaskCreate(title="Test", status=TaskStatus.TODO)
        self.assertEqual(task_create.status, TaskStatus.TODO)


class TestTaskUpdate(unittest.TestCase):
    """Tests for TaskUpdate model"""

    def test_all_fields_optional(self) -> None:
        """Test that all fields are optional"""
        task_update = TaskUpdate()
        self.assertIsNone(task_update.title)
        self.assertIsNone(task_update.description)
        self.assertIsNone(task_update.status)

    def test_partial_update_title(self) -> None:
        """Test updating only title"""
        task_update = TaskUpdate(title="New Title")
        self.assertEqual(task_update.title, "New Title")
        self.assertIsNone(task_update.description)
        self.assertIsNone(task_update.status)

    def test_partial_update_status(self) -> None:
        """Test updating only status"""
        task_update = TaskUpdate(status=TaskStatus.DONE)
        self.assertIsNone(task_update.title)
        self.assertEqual(task_update.status, TaskStatus.DONE)

    def test_update_title_validation(self) -> None:
        """Test that title validation works in updates"""
        with self.assertRaises(ValidationError):
            TaskUpdate(title="")


class TestTask(unittest.TestCase):
    """Tests for Task model"""

    def test_valid_task(self) -> None:
        """Test creating valid Task"""
        task = Task(
            id=1,
            title="Test Task",
            description="Description",
            status=TaskStatus.TODO,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )

        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, TaskStatus.TODO)

    def test_id_must_be_positive(self) -> None:
        """Test that ID must be >= 1"""
        with self.assertRaises(ValidationError):
            Task(id=0, title="Test", status=TaskStatus.BACKLOG)

    def test_timestamps_auto_generated(self) -> None:
        """Test that timestamps are auto-generated"""
        task = Task(id=1, title="Test", status=TaskStatus.BACKLOG)

        self.assertIsInstance(task.created_at, datetime)
        self.assertIsInstance(task.updated_at, datetime)


if __name__ == "__main__":
    unittest.main()
