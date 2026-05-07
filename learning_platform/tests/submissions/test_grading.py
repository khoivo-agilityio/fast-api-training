"""
Tests for grading helpers — pure static method tests, no DB needed.

grade_answer and compute_score were moved from src.submissions.grading
into SubmissionService as private static methods. Tests call them via the
class directly (no DB session needed for @staticmethod).
"""

from src.submissions.service import SubmissionService


class TestGradeAnswer:
    """Tests for SubmissionService._grade_answer."""

    def test_exact_match(self):
        """Exact match returns True."""
        assert SubmissionService._grade_answer("Paris", "Paris") is True

    def test_case_insensitive(self):
        """Case-insensitive match returns True."""
        assert SubmissionService._grade_answer("Paris", "paris") is True
        assert SubmissionService._grade_answer("PARIS", "paris") is True

    def test_wrong_answer(self):
        """Wrong answer returns False."""
        assert SubmissionService._grade_answer("Paris", "London") is False

    def test_whitespace_trimmed(self):
        """Leading/trailing whitespace is trimmed before comparison."""
        assert SubmissionService._grade_answer("Paris", "  Paris  ") is True
        assert SubmissionService._grade_answer("  Paris  ", "Paris") is True


class TestComputeScore:
    """Tests for SubmissionService._compute_score."""

    def test_all_correct(self):
        """All correct → 100.0."""
        assert SubmissionService._compute_score(5, 5) == 100.0

    def test_partial(self):
        """Partial → correct percentage rounded to 2dp."""
        assert SubmissionService._compute_score(2, 3) == 66.67

    def test_zero_total(self):
        """Zero total → 0.0 (avoids ZeroDivisionError)."""
        assert SubmissionService._compute_score(0, 0) == 0.0

    def test_none_correct(self):
        """No correct answers → 0.0."""
        assert SubmissionService._compute_score(0, 5) == 0.0
