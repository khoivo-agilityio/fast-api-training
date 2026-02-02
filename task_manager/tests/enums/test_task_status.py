import unittest

from enums import TaskStatus


class TestTaskStatus(unittest.TestCase):
    """Test cases for TaskStatus enum"""

    def test_from_string_valid(self) -> None:
        """Test parsing valid status strings"""
        self.assertEqual(TaskStatus.from_string("todo"), TaskStatus.TODO)
        self.assertEqual(TaskStatus.from_string("TODO"), TaskStatus.TODO)
        self.assertEqual(TaskStatus.from_string("in-progress"), TaskStatus.IN_PROGRESS)
        self.assertEqual(TaskStatus.from_string("IN_PROGRESS"), TaskStatus.IN_PROGRESS)

    def test_from_string_invalid(self) -> None:
        """Test parsing invalid status strings raises ValueError"""
        with self.assertRaises(ValueError):
            TaskStatus.from_string("invalid")

    def test_can_transition_to_valid(self) -> None:
        """Test valid status transitions"""
        # BACKLOG can go to TODO or IN_PROGRESS
        self.assertTrue(TaskStatus.BACKLOG.can_transition_to(TaskStatus.TODO))
        self.assertTrue(TaskStatus.BACKLOG.can_transition_to(TaskStatus.IN_PROGRESS))

        # TODO can go to BACKLOG or IN_PROGRESS
        self.assertTrue(TaskStatus.TODO.can_transition_to(TaskStatus.BACKLOG))
        self.assertTrue(TaskStatus.TODO.can_transition_to(TaskStatus.IN_PROGRESS))

        # IN_PROGRESS can go to TODO, TESTING, or DONE
        self.assertTrue(TaskStatus.IN_PROGRESS.can_transition_to(TaskStatus.TODO))
        self.assertTrue(TaskStatus.IN_PROGRESS.can_transition_to(TaskStatus.TESTING))
        self.assertTrue(TaskStatus.IN_PROGRESS.can_transition_to(TaskStatus.DONE))

        # TESTING can go to IN_PROGRESS or DONE
        self.assertTrue(TaskStatus.TESTING.can_transition_to(TaskStatus.IN_PROGRESS))
        self.assertTrue(TaskStatus.TESTING.can_transition_to(TaskStatus.DONE))

    def test_can_transition_to_invalid(self) -> None:
        """Test invalid status transitions"""
        # Cannot go from BACKLOG directly to DONE
        self.assertFalse(TaskStatus.BACKLOG.can_transition_to(TaskStatus.DONE))

        # Cannot go from DONE to anything
        self.assertFalse(TaskStatus.DONE.can_transition_to(TaskStatus.TODO))
        self.assertFalse(TaskStatus.DONE.can_transition_to(TaskStatus.BACKLOG))

    def test_can_transition_to_same_status(self) -> None:
        """Test that same status transition is always valid"""
        for status in TaskStatus:
            self.assertTrue(status.can_transition_to(status))

    def test_get_valid_transitions(self) -> None:
        """Test getting list of valid transitions"""
        self.assertEqual(
            TaskStatus.BACKLOG.get_valid_transitions(),
            [TaskStatus.TODO, TaskStatus.IN_PROGRESS],
        )
        self.assertEqual(TaskStatus.DONE.get_valid_transitions(), [])

    def test_is_final(self) -> None:
        """Test is_final property"""
        self.assertTrue(TaskStatus.DONE.is_final)
        self.assertFalse(TaskStatus.TODO.is_final)
        self.assertFalse(TaskStatus.BACKLOG.is_final)

    def test_is_active(self) -> None:
        """Test is_active property"""
        self.assertTrue(TaskStatus.TODO.is_active)
        self.assertTrue(TaskStatus.IN_PROGRESS.is_active)
        self.assertTrue(TaskStatus.TESTING.is_active)
        self.assertFalse(TaskStatus.BACKLOG.is_active)
        self.assertFalse(TaskStatus.DONE.is_active)

    def test_is_pending(self) -> None:
        """Test is_pending property"""
        self.assertTrue(TaskStatus.BACKLOG.is_pending)
        self.assertTrue(TaskStatus.TODO.is_pending)
        self.assertFalse(TaskStatus.IN_PROGRESS.is_pending)
        self.assertFalse(TaskStatus.DONE.is_pending)

    def test_get_transition_error_message(self) -> None:
        """Test error message generation"""
        error_msg = TaskStatus.BACKLOG.get_transition_error_message(TaskStatus.DONE)
        self.assertIn("Invalid status transition", error_msg)
        self.assertIn("backlog", error_msg)
        self.assertIn("done", error_msg)
        self.assertIn("todo", error_msg)  # Should mention valid transitions


if __name__ == "__main__":
    unittest.main()
