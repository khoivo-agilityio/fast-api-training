"""Unit tests for TaskService"""

import unittest
from datetime import datetime

from pydantic import ValidationError

from src.task_manager.models import Task, TaskStatus
from src.task_manager.services import TaskService
from src.task_manager.storage.task_repo import TaskRepository


class MockTaskRepository(TaskRepository):
    """Mock repository for testing"""

    def __init__(self) -> None:
        self.tasks: list[Task] = []
        self.next_id = 1

    def add(self, task: Task) -> Task:
        task = Task(
            id=self.next_id,
            title=task.title,
            description=task.description,
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        self.tasks.append(task)
        self.next_id += 1
        return task

    def list(self) -> list[Task]:
        return self.tasks.copy()

    def get_by_id(self, task_id: int) -> Task | None:
        return next((t for t in self.tasks if t.id == task_id), None)

    def update(self, task: Task) -> Task | None:
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                return task
        return None

    def delete(self, task_id: int) -> bool:
        initial_length = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        return len(self.tasks) < initial_length


class TestTaskService(unittest.TestCase):
    """Test cases for TaskService"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.repo = MockTaskRepository()
        self.service = TaskService(self.repo)

    def test_add_task_with_valid_data(self) -> None:
        """Test adding a task with valid data"""
        task = self.service.add("Test Task", "Description")

        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.description, "Description")
        self.assertEqual(task.status, TaskStatus.BACKLOG)
        self.assertIsInstance(task.created_at, datetime)
        self.assertIsInstance(task.updated_at, datetime)

    def test_add_task_strips_whitespace(self) -> None:
        """Test that add_task strips whitespace from title and description"""
        task = self.service.add("  Test Task  ", "  Description  ")

        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.description, "Description")

    def test_add_task_empty_title_raises_error(self) -> None:
        """Test that empty title raises ValidationError"""
        with self.assertRaises(ValidationError):
            self.service.add("")

    def test_add_task_whitespace_only_title_raises_error(self) -> None:
        """Test that whitespace-only title raises ValidationError"""
        with self.assertRaises(ValidationError):
            self.service.add("   ")

    def test_add_task_without_description(self) -> None:
        """Test adding a task without description"""
        task = self.service.add("Test Task")

        self.assertIsNone(task.description)

    def test_add_task_with_custom_status(self) -> None:
        """Test adding a task with custom initial status"""
        task = self.service.add("Test Task", status=TaskStatus.TODO)

        self.assertEqual(task.status, TaskStatus.TODO)

    def test_list_all_returns_all_tasks(self) -> None:
        """Test that list_all returns all tasks"""
        self.service.add("Task 1")
        self.service.add("Task 2")
        self.service.add("Task 3")

        tasks = self.service.list_all()

        self.assertEqual(len(tasks), 3)

    def test_list_by_status_filters_correctly(self) -> None:
        """Test that list_by_status filters tasks correctly"""
        self.service.add("Task 1", status=TaskStatus.BACKLOG)
        self.service.add("Task 2", status=TaskStatus.TODO)
        self.service.add("Task 3", status=TaskStatus.TODO)

        todo_tasks = self.service.list_by_status(TaskStatus.TODO)

        self.assertEqual(len(todo_tasks), 2)
        self.assertTrue(all(t.status == TaskStatus.TODO for t in todo_tasks))

    def test_get_task_returns_correct_task(self) -> None:
        """Test that get_task returns the correct task"""
        task = self.service.add("Test Task")

        retrieved = self.service.get(task.id)

        self.assertEqual(retrieved.id, task.id)
        self.assertEqual(retrieved.title, task.title)

    def test_get_task_nonexistent_raises_error(self) -> None:
        """Test that getting nonexistent task raises ValueError"""
        with self.assertRaises(ValueError) as context:
            self.service.get(999)

        self.assertIn("not found", str(context.exception))

    def test_update_task_title(self) -> None:
        """Test updating task title"""
        task = self.service.add("Original Title")

        updated = self.service.update(task.id, title="New Title")

        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.description, task.description)
        self.assertEqual(updated.status, task.status)

    def test_update_task_description(self) -> None:
        """Test updating task description"""
        task = self.service.add("Test", "Original")

        updated = self.service.update(task.id, description="New Description")

        self.assertEqual(updated.description, "New Description")

    def test_update_task_empty_title_raises_error(self) -> None:
        """Test that updating with empty title raises ValidationError"""
        task = self.service.add("Original")

        with self.assertRaises(ValidationError):
            self.service.update(task.id, title="")

    def test_update_task_status_valid_transition(self) -> None:
        """Test updating task status with valid transition"""
        task = self.service.add("Test")

        updated = self.service.update(task.id, status=TaskStatus.TODO)

        self.assertEqual(updated.status, TaskStatus.TODO)

    def test_update_task_status_invalid_transition(self) -> None:
        """Test that invalid status transition raises ValueError"""
        task = self.service.add("Test")  # BACKLOG

        with self.assertRaises(ValueError) as context:
            self.service.update(task.id, status=TaskStatus.DONE)

        self.assertIn("Invalid status transition", str(context.exception))

    def test_update_task_updates_timestamp(self) -> None:
        """Test that update_task updates the updated_at timestamp"""
        task = self.service.add("Test")
        original_updated = task.updated_at

        import time

        time.sleep(0.01)  # Ensure time passes

        updated = self.service.update(task.id, title="Updated")

        self.assertGreater(updated.updated_at, original_updated)

    def test_mark_as_done_success(self) -> None:
        """Test marking a task as done successfully"""
        task = self.service.add("Test")
        self.service.update(task.id, status=TaskStatus.TODO)
        self.service.update(task.id, status=TaskStatus.IN_PROGRESS)
        self.service.update(task.id, status=TaskStatus.TESTING)

        done_task = self.service.mark_as_done(task.id)

        self.assertEqual(done_task.status, TaskStatus.DONE)

    def test_mark_as_done_already_done_raises_error(self) -> None:
        """Test that marking already done task raises ValueError"""
        task = self.service.add("Test")
        self.service.update(task.id, status=TaskStatus.IN_PROGRESS)
        self.service.mark_as_done(task.id)

        with self.assertRaises(ValueError) as context:
            self.service.mark_as_done(task.id)

        self.assertIn("already marked as DONE", str(context.exception))

    def test_mark_as_done_invalid_transition_raises_error(self) -> None:
        """Test that marking done from invalid status raises ValueError"""
        task = self.service.add("Test")  # BACKLOG

        with self.assertRaises(ValueError) as context:
            self.service.mark_as_done(task.id)

        self.assertIn("Cannot mark task as DONE", str(context.exception))

    def test_delete_task_success(self) -> None:
        """Test deleting a task successfully"""
        task = self.service.add("Test")

        result = self.service.delete(task.id)

        self.assertTrue(result)
        with self.assertRaises(ValueError):
            self.service.get(task.id)

    def test_delete_task_nonexistent_raises_error(self) -> None:
        """Test that deleting nonexistent task raises ValueError"""
        with self.assertRaises(ValueError):
            self.service.delete(999)

    def test_get_summary_empty(self) -> None:
        """Test get_summary with no tasks"""
        summary = self.service.get_summary()

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["completion_percentage"], 0.0)

    def test_get_summary_with_tasks(self) -> None:
        """Test get_summary with various tasks"""
        self.service.add("Task 1", status=TaskStatus.BACKLOG)
        self.service.add("Task 2", status=TaskStatus.TODO)
        self.service.add("Task 3", status=TaskStatus.IN_PROGRESS)
        task4 = self.service.add("Task 4", status=TaskStatus.IN_PROGRESS)
        self.service.mark_as_done(task4.id)

        summary = self.service.get_summary()

        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["backlog"], 1)
        self.assertEqual(summary["todo"], 1)
        self.assertEqual(summary["in_progress"], 1)
        self.assertEqual(summary["done"], 1)
        self.assertEqual(summary["completion_percentage"], 25.0)


if __name__ == "__main__":
    unittest.main()
