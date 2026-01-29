"""
Integration tests for CLI commands.

These tests verify that CLI commands work correctly with the service layer.
"""

import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner, Result

from src.task_manager.cli import app

runner = CliRunner()


class TestCLICommands(unittest.TestCase):
    """Integration tests for CLI commands"""

    def setUp(self) -> None:
        """Set up test fixtures - use temporary file for each test"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp:
            temp_name = temp.name
        self.data_file = Path(temp_name)

    def tearDown(self) -> None:
        """Clean up temporary file"""
        if self.data_file.exists():
            self.data_file.unlink()

    # ========================================================================
    # HELPER METHODS - DRY PRINCIPLE
    # ========================================================================

    def invoke_command(self, *args: str) -> Result:
        """
        Invoke CLI command with automatic data file injection.

        Args:
            *args: Command arguments (e.g., "add", "Task Title")

        Returns:
            Result object from CLI runner
        """
        cmd_args = list(args) + ["--file", str(self.data_file)]
        return runner.invoke(app, cmd_args)

    def assert_success(self, result: Result, *expected_texts: str) -> None:
        """
        Assert command succeeded and contains expected text.

        Args:
            result: CLI result object
            *expected_texts: Text strings that should be in output
        """
        self.assertEqual(result.exit_code, 0, f"Command failed: {result.stdout}")
        for text in expected_texts:
            self.assertIn(text, result.stdout)

    def assert_failure(self, result: Result, *expected_texts: str) -> None:
        """
        Assert command failed and contains expected error text.

        Args:
            result: CLI result object
            *expected_texts: Error text strings that should be in output
        """
        self.assertNotEqual(result.exit_code, 0, "Command should have failed")
        for text in expected_texts:
            self.assertIn(text, result.stdout)

    def add_task(self, title: str, description: str | None = None) -> Result:
        """
        Helper to add a task via CLI.

        Args:
            title: Task title
            description: Optional task description

        Returns:
            Result object from CLI runner
        """
        args = ["add", title]
        if description:
            args.extend(["--description", description])
        return self.invoke_command(*args)

    def update_task_status(self, task_id: int, status: str) -> Result:
        """
        Helper to update task status.

        Args:
            task_id: ID of task to update
            status: New status value

        Returns:
            Result object from CLI runner
        """
        return self.invoke_command("update", str(task_id), "--status", status)

    def create_test_tasks(self, count: int = 3) -> None:
        """
        Helper to create multiple test tasks.

        Args:
            count: Number of tasks to create
        """
        for i in range(1, count + 1):
            self.add_task(f"Task {i}")

    def setup_task_with_status(self, title: str, status: str) -> int:
        """
        Helper to create a task and set its status.

        Args:
            title: Task title
            status: Desired status

        Returns:
            Task ID (always 1 for single task)
        """
        self.add_task(title)
        if status != "backlog":
            self.update_task_status(1, status)
        return 1

    # ========================================================================
    # TEST CASES - ADD COMMAND
    # ========================================================================

    def test_add_command_success(self) -> None:
        """Test adding a task via CLI"""
        result = self.add_task("Test Task")
        self.assert_success(result, "Task created successfully", "Test Task")

    def test_add_command_with_description(self) -> None:
        """Test adding a task with description"""
        result = self.add_task("Test Task", "Test Description")
        self.assert_success(result, "Test Description")

    def test_add_command_empty_title_fails(self) -> None:
        """Test that empty title is rejected"""
        result = self.add_task("")
        self.assert_failure(result, "Error")

    # ========================================================================
    # TEST CASES - LIST COMMAND
    # ========================================================================

    def test_list_command_empty(self) -> None:
        """Test listing tasks when none exist"""
        result = self.invoke_command("list")
        self.assert_success(result, "No tasks yet")

    def test_list_command_with_tasks(self) -> None:
        """Test listing tasks"""
        self.create_test_tasks(2)
        result = self.invoke_command("list")
        self.assert_success(result, "Task 1", "Task 2", "2 total")

    def test_list_command_with_status_filter(self) -> None:
        """Test filtering tasks by status"""
        # Add first task and update to TODO
        add_result = self.add_task("Task 1")
        self.assertEqual(
            add_result.exit_code, 0, f"Failed to add Task 1: {add_result.stdout}"
        )

        update_result = self.update_task_status(1, "todo")
        self.assertEqual(
            update_result.exit_code,
            0,
            f"Failed to update to TODO: {update_result.stdout}",
        )

        # Add second task (stays in BACKLOG)
        add_result2 = self.add_task("Task 2")
        self.assertEqual(
            add_result2.exit_code, 0, f"Failed to add Task 2: {add_result2.stdout}"
        )

        # Filter by TODO status
        result = self.invoke_command("list", "--status", "todo")
        self.assert_success(result, "Task 1")
        self.assertNotIn(
            "Task 2",
            result.stdout,
            f"Task 2 should not be in TODO list:\n{result.stdout}",
        )

    # ========================================================================
    # TEST CASES - SHOW COMMAND
    # ========================================================================

    def test_show_command(self) -> None:
        """Test showing a single task"""
        self.add_task("Test Task", "Test Desc")
        result = self.invoke_command("show", "1")
        self.assert_success(result, "Task #1", "Test Task", "Test Desc")

    def test_show_command_not_found(self) -> None:
        """Test showing non-existent task"""
        result = self.invoke_command("show", "999")
        self.assert_failure(result, "Error", "not found")

    # ========================================================================
    # TEST CASES - UPDATE COMMAND
    # ========================================================================

    def test_update_command_title(self) -> None:
        """Test updating task title"""
        self.add_task("Old Title")
        result = self.invoke_command("update", "1", "--title", "New Title")
        self.assert_success(result, "updated successfully", "New Title")

    def test_update_command_status(self) -> None:
        """Test updating task status"""
        self.add_task("Task")
        result = self.update_task_status(1, "todo")
        self.assert_success(result, "TODO")

    def test_update_command_invalid_transition(self) -> None:
        """Test invalid status transition"""
        # Create task
        add_result = self.add_task("Task")
        self.assertEqual(add_result.exit_code, 0, f"Add failed: {add_result.stdout}")

        # Move to in-progress
        update1 = self.update_task_status(1, "in-progress")
        self.assertEqual(
            update1.exit_code, 0, f"Update to in-progress failed: {update1.stdout}"
        )

        # Mark as done
        done_result = self.invoke_command("done", "1")
        self.assertEqual(
            done_result.exit_code, 0, f"Mark as done failed: {done_result.stdout}"
        )

        # Try to transition from DONE to TODO (invalid)
        result = self.update_task_status(1, "todo")
        self.assert_failure(result, "Error")
        # Check for either "Invalid" or "Cannot" in error message
        self.assertTrue(
            "Invalid" in result.stdout or "Cannot" in result.stdout,
            f"Expected transition error message in:\n{result.stdout}",
        )

    # ========================================================================
    # TEST CASES - DONE COMMAND
    # ========================================================================

    def test_done_command(self) -> None:
        """Test marking task as done"""
        # Create task
        add_result = self.add_task("Task")
        self.assertEqual(add_result.exit_code, 0, f"Add failed: {add_result.stdout}")

        # Move to in-progress first (required for valid transition to done)
        update_result = self.update_task_status(1, "in-progress")
        self.assertEqual(
            update_result.exit_code, 0, f"Update failed: {update_result.stdout}"
        )

        # Mark as done
        result = self.invoke_command("done", "1")
        self.assert_success(result, "marked as done successfully")

    def test_done_command_already_done(self) -> None:
        """Test marking already done task"""
        # Create task
        add_result = self.add_task("Task")
        self.assertEqual(add_result.exit_code, 0, f"Add failed: {add_result.stdout}")

        # Move to in-progress
        update_result = self.update_task_status(1, "in-progress")
        self.assertEqual(
            update_result.exit_code, 0, f"Update failed: {update_result.stdout}"
        )

        # Mark as done
        done_result = self.invoke_command("done", "1")
        self.assertEqual(
            done_result.exit_code, 0, f"First done failed: {done_result.stdout}"
        )

        # Try to mark as done again
        result = self.invoke_command("done", "1")
        self.assert_failure(result, "Error")
        # Check for "already" or "DONE" in error message
        self.assertTrue(
            "already" in result.stdout or "DONE" in result.stdout,
            f"Expected 'already done' error in:\n{result.stdout}",
        )

    # ========================================================================
    # TEST CASES - REMOVE COMMAND
    # ========================================================================

    def test_remove_command_with_force(self) -> None:
        """Test removing task with force flag"""
        self.add_task("Task")

        result = self.invoke_command("remove", "1", "--force")
        self.assert_success(result, "deleted successfully")

        # Verify task is gone
        list_result = self.invoke_command("list")
        self.assertIn("No tasks yet", list_result.stdout)

    # ========================================================================
    # TEST CASES - SUMMARY COMMAND
    # ========================================================================

    def test_summary_command_empty(self) -> None:
        """Test summary with no tasks"""
        result = self.invoke_command("summary")
        self.assert_success(result, "Task Summary", "0")

    def test_summary_command_with_tasks(self) -> None:
        """Test summary with various task statuses"""
        # Create tasks
        self.create_test_tasks(3)

        # Update statuses
        update1 = self.update_task_status(1, "todo")
        self.assertEqual(update1.exit_code, 0, f"Update 1 failed: {update1.stdout}")

        update2 = self.update_task_status(2, "in-progress")
        self.assertEqual(update2.exit_code, 0, f"Update 2 failed: {update2.stdout}")

        done_result = self.invoke_command("done", "2")
        self.assertEqual(done_result.exit_code, 0, f"Done failed: {done_result.stdout}")

        # Get summary
        result = self.invoke_command("summary")
        self.assert_success(result, "Task Summary", "Total Tasks", "3", "Completion")


if __name__ == "__main__":
    unittest.main()
