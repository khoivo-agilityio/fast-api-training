"""Unit tests for TaskService"""

import unittest
from datetime import datetime

from pydantic import ValidationError

from src.task_manager.enums import TaskStatus
from src.task_manager.models import Task, TaskSummary
from src.task_manager.repositories import TaskRepository
from src.task_manager.services import TaskService


class MockTaskRepository(TaskRepository):
    """
    Mock repository for testing without JSON serialization.

    This mock stores tasks in memory as Task objects, preserving enum types.
    """

    def __init__(self) -> None:
        """Initialize mock repository with empty task list"""
        self.tasks: list[Task] = []
        self.next_id = 1

    def add(self, task: Task) -> Task:
        """Add a task to the mock repository."""
        # Create new task with auto-generated ID, ensuring status is enum
        new_task = Task(
            id=self.next_id,
            title=task.title,
            description=task.description,
            status=self._ensure_enum(task.status),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
        self.tasks.append(new_task)
        self.next_id += 1
        return self._ensure_task_enum_status(new_task)

    def list_all(self) -> list[Task]:
        """Get all tasks."""
        return [self._ensure_task_enum_status(t) for t in self.tasks.copy()]

    def get_by_id(self, task_id: int) -> Task | None:
        """Get a task by ID."""
        task = next((t for t in self.tasks if t.id == task_id), None)
        return self._ensure_task_enum_status(task) if task else None

    def update(self, task: Task) -> Task | None:
        """Update a task in the repository."""
        for i, existing_task in enumerate(self.tasks):
            if existing_task.id == task.id:
                # Update ensuring status is enum
                updated_task = Task(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    status=self._ensure_enum(task.status),
                    created_at=existing_task.created_at,
                    updated_at=task.updated_at,
                )
                self.tasks[i] = updated_task
                return self._ensure_task_enum_status(updated_task)
        return None

    def delete(self, task_id: int) -> bool:
        """Delete a task by ID."""
        initial_length = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.id != task_id]
        return len(self.tasks) < initial_length

    @staticmethod
    def _ensure_enum(status: TaskStatus | str) -> TaskStatus:
        """Ensure status is a TaskStatus enum."""
        if isinstance(status, TaskStatus):
            return status
        return TaskStatus(status)

    @staticmethod
    def _ensure_task_enum_status(task: Task) -> Task:
        """
        Ensure task's status is an enum, not a string.

        Pydantic may serialize enum to string, so we recreate the task
        with enum status to ensure service layer gets proper enum objects.
        """
        if isinstance(task.status, TaskStatus):
            return task

        # Recreate task with enum status
        return Task(
            id=task.id,
            title=task.title,
            description=task.description,
            status=TaskStatus(task.status),
            created_at=task.created_at,
            updated_at=task.updated_at,
        )


class TestTaskService(unittest.TestCase):
    """Test cases for TaskService"""

    def setUp(self) -> None:
        """Set up test fixtures"""
        self.repo = MockTaskRepository()
        self.service = TaskService(self.repo)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _get_status(self, task: Task) -> TaskStatus:
        """
        Get task status as enum, converting from string if necessary.

        This handles the case where Pydantic serializes enum to string.
        """
        if isinstance(task.status, TaskStatus):
            return task.status
        return TaskStatus(task.status)

    def assert_status_equals(self, task: Task, expected: TaskStatus) -> None:
        """Assert task has expected status (handling string/enum)."""
        actual_status = self._get_status(task)
        self.assertEqual(actual_status, expected)

    # ========================================================================
    # TEST CASES - ADD COMMAND
    # ========================================================================

    def test_add_task_with_valid_data(self) -> None:
        """Test adding a task with valid data"""
        task = self.service.add("Test Task", "Description")

        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.description, "Description")
        self.assert_status_equals(task, TaskStatus.BACKLOG)
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

        self.assert_status_equals(task, TaskStatus.TODO)

    # ========================================================================
    # TEST CASES - LIST COMMANDS
    # ========================================================================

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
        for task in todo_tasks:
            self.assert_status_equals(task, TaskStatus.TODO)

    # ========================================================================
    # TEST CASES - GET COMMAND
    # ========================================================================

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

    # ========================================================================
    # TEST CASES - UPDATE COMMAND
    # ========================================================================

    def test_update_task_title(self) -> None:
        """Test updating task title"""
        task = self.service.add("Original Title")

        updated = self.service.update(task.id, title="New Title")

        self.assertEqual(updated.title, "New Title")
        self.assertEqual(updated.description, task.description)
        self.assert_status_equals(updated, self._get_status(task))

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

        self.assert_status_equals(updated, TaskStatus.TODO)

    def test_update_task_status_invalid_transition(self) -> None:
        """Test that invalid status transition raises ValueError"""
        task = self.service.add("Test")  # BACKLOG

        with self.assertRaises(ValueError) as context:
            self.service.update(task.id, status=TaskStatus.DONE)

        error_msg = str(context.exception)
        self.assertTrue(
            "Invalid status transition" in error_msg or "Cannot" in error_msg,
            f"Expected transition error, got: {error_msg}",
        )

    def test_update_task_updates_timestamp(self) -> None:
        """Test that update_task updates the updated_at timestamp"""
        task = self.service.add("Test")
        original_updated = task.updated_at

        import time

        time.sleep(0.01)

        updated = self.service.update(task.id, title="Updated")

        self.assertGreater(updated.updated_at, original_updated)

    # ========================================================================
    # TEST CASES - MARK AS DONE
    # ========================================================================

    def test_mark_as_done_success(self) -> None:
        """Test marking a task as done successfully"""
        task = self.service.add("Test")

        # Valid transition path: BACKLOG -> TODO -> IN_PROGRESS -> DONE
        self.service.update(task.id, status=TaskStatus.TODO)
        self.service.update(task.id, status=TaskStatus.IN_PROGRESS)

        done_task = self.service.mark_as_done(task.id)

        self.assert_status_equals(done_task, TaskStatus.DONE)

    def test_mark_as_done_already_done_raises_error(self) -> None:
        """Test that marking already done task raises ValueError"""
        task = self.service.add("Test")

        # Move to IN_PROGRESS then mark as done
        self.service.update(task.id, status=TaskStatus.IN_PROGRESS)
        self.service.mark_as_done(task.id)

        # Verify task is done
        done_task = self.service.get(task.id)
        self.assert_status_equals(done_task, TaskStatus.DONE)

        # Try to mark as done again
        with self.assertRaises(ValueError) as context:
            self.service.mark_as_done(task.id)

        error_msg = str(context.exception)
        self.assertTrue(
            "already marked as DONE" in error_msg or "already" in error_msg.lower(),
            f"Expected 'already done' error, got: {error_msg}",
        )

    def test_mark_as_done_invalid_transition_raises_error(self) -> None:
        """Test that marking done from invalid status raises ValueError"""
        task = self.service.add("Test")  # BACKLOG

        with self.assertRaises(ValueError) as context:
            self.service.mark_as_done(task.id)

        error_msg = str(context.exception)
        self.assertTrue(
            "Cannot mark task as DONE" in error_msg or "Invalid" in error_msg,
            f"Expected transition error, got: {error_msg}",
        )

    # ========================================================================
    # TEST CASES - DELETE COMMAND
    # ========================================================================

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

    # ========================================================================
    # TEST CASES - SUMMARY
    # ========================================================================

    def test_get_summary_empty(self) -> None:
        """Test get_summary with no tasks"""
        summary = self.service.get_summary()

        # Verify it's a TaskSummary object
        self.assertIsInstance(summary, TaskSummary)

        # Check all fields for empty summary
        self.assertEqual(summary.total, 0)
        self.assertEqual(summary.backlog, 0)
        self.assertEqual(summary.todo, 0)
        self.assertEqual(summary.in_progress, 0)
        self.assertEqual(summary.testing, 0)
        self.assertEqual(summary.done, 0)
        self.assertEqual(summary.active_tasks, 0)
        self.assertEqual(summary.pending_tasks, 0)
        self.assertEqual(summary.completion_percentage, 0.0)

    def test_get_summary_with_tasks(self) -> None:
        """Test get_summary with various tasks"""
        # Create tasks with different statuses
        self.service.add("Task 1", status=TaskStatus.BACKLOG)
        self.service.add("Task 2", status=TaskStatus.TODO)
        self.service.add("Task 3", status=TaskStatus.IN_PROGRESS)
        task4 = self.service.add("Task 4", status=TaskStatus.IN_PROGRESS)

        # Mark task4 as done
        self.service.mark_as_done(task4.id)

        summary = self.service.get_summary()

        # Verify it's a TaskSummary object
        self.assertIsInstance(summary, TaskSummary)

        # Check all status counts
        self.assertEqual(summary.total, 4)
        self.assertEqual(summary.backlog, 1)
        self.assertEqual(summary.todo, 1)
        self.assertEqual(summary.in_progress, 1)
        self.assertEqual(summary.testing, 0)
        self.assertEqual(summary.done, 1)

        # Check computed fields
        # active_tasks = TODO + IN_PROGRESS + TESTING = 1 + 1 + 0 = 2
        self.assertEqual(summary.active_tasks, 2)
        # pending_tasks = BACKLOG + TODO = 1 + 1 = 2
        self.assertEqual(summary.pending_tasks, 2)
        # completion_percentage = (1 / 4) * 100 = 25.0
        self.assertEqual(summary.completion_percentage, 25.0)

    def test_get_summary_all_done(self) -> None:
        """Test get_summary when all tasks are done"""
        task1 = self.service.add("Task 1", status=TaskStatus.IN_PROGRESS)
        task2 = self.service.add("Task 2", status=TaskStatus.IN_PROGRESS)

        self.service.mark_as_done(task1.id)
        self.service.mark_as_done(task2.id)

        summary = self.service.get_summary()

        self.assertIsInstance(summary, TaskSummary)
        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.done, 2)
        self.assertEqual(summary.active_tasks, 0)
        self.assertEqual(summary.pending_tasks, 0)
        self.assertEqual(summary.completion_percentage, 100.0)

    def test_get_summary_with_testing_status(self) -> None:
        """Test get_summary includes testing status in active tasks"""
        self.service.add("Task 1", status=TaskStatus.TESTING)
        self.service.add("Task 2", status=TaskStatus.TODO)

        summary = self.service.get_summary()

        self.assertIsInstance(summary, TaskSummary)
        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.testing, 1)
        self.assertEqual(summary.todo, 1)
        # active_tasks should include TESTING
        self.assertEqual(summary.active_tasks, 2)
        self.assertEqual(summary.pending_tasks, 1)  # Only TODO
        self.assertEqual(summary.completion_percentage, 0.0)

    def test_get_summary_percentage_rounding(self) -> None:
        """Test that completion percentage is rounded correctly"""
        # Create 3 tasks, complete 1 -> 33.333... should round to 33.33
        self.service.add("Task 1", status=TaskStatus.BACKLOG)
        self.service.add("Task 2", status=TaskStatus.BACKLOG)
        task3 = self.service.add("Task 3", status=TaskStatus.IN_PROGRESS)

        self.service.mark_as_done(task3.id)

        summary = self.service.get_summary()

        self.assertIsInstance(summary, TaskSummary)
        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.done, 1)
        # 1/3 * 100 = 33.333... should round to 33.33
        self.assertAlmostEqual(summary.completion_percentage, 33.33, places=2)


if __name__ == "__main__":
    unittest.main()
