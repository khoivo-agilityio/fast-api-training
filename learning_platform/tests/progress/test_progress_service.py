"""
Tests for ProgressService — unit-level service tests.

All tests use an in-memory aiosqlite session from conftest.
Progress records are created via the service to exercise real logic,
or directly via helpers to set up preconditions.
"""

import pytest

from src.progress.models import ProgressStatus
from src.progress.service import ProgressService
from tests.conftest import (
    create_test_course,
    create_test_enrollment,
    create_test_instructor,
    create_test_lesson,
    create_test_progress,
    create_test_user,
)


class TestTouch:
    """Tests for ProgressService.touch()."""

    async def test_touch_creates_in_progress(self, async_session):
        """First visit to a lesson WITH a quiz → status=in_progress."""
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        student = await create_test_user(async_session, email="s1@test.com")

        service = ProgressService(async_session)
        progress = await service.touch(student["user"].id, lesson.id, has_quiz=True)

        assert progress.status == ProgressStatus.IN_PROGRESS
        assert progress.completed_at is None

    async def test_touch_no_quiz_auto_completes(self, async_session):
        """First visit to a lesson WITHOUT a quiz → status=completed."""
        instructor = await create_test_instructor(async_session, email="i2@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 2")
        lesson = await create_test_lesson(async_session, course.id, title="L2")
        student = await create_test_user(async_session, email="s2@test.com")

        service = ProgressService(async_session)
        progress = await service.touch(student["user"].id, lesson.id, has_quiz=False)

        assert progress.status == ProgressStatus.COMPLETED
        assert progress.completed_at is not None

    async def test_touch_idempotent_does_not_regress(self, async_session):
        """Calling touch() on an already-completed lesson keeps status=completed."""
        instructor = await create_test_instructor(async_session, email="i3@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 3")
        lesson = await create_test_lesson(async_session, course.id, title="L3")
        student = await create_test_user(async_session, email="s3@test.com")

        # Seed a completed record
        await create_test_progress(
            async_session, student["user"].id, lesson.id, status="completed"
        )

        service = ProgressService(async_session)
        # Call touch with has_quiz=True — must NOT regress to in_progress
        progress = await service.touch(student["user"].id, lesson.id, has_quiz=True)

        assert progress.status == ProgressStatus.COMPLETED

    async def test_touch_in_progress_no_quiz_completes(self, async_session):
        """in_progress + has_quiz=False → transitions to completed."""
        instructor = await create_test_instructor(async_session, email="i4@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 4")
        lesson = await create_test_lesson(async_session, course.id, title="L4")
        student = await create_test_user(async_session, email="s4@test.com")

        # Seed in_progress (simulates lesson whose quiz was later removed)
        await create_test_progress(
            async_session, student["user"].id, lesson.id, status="in_progress"
        )

        service = ProgressService(async_session)
        progress = await service.touch(student["user"].id, lesson.id, has_quiz=False)

        assert progress.status == ProgressStatus.COMPLETED
        assert progress.completed_at is not None


class TestMarkLessonCompleted:
    """Tests for ProgressService.mark_lesson_completed()."""

    async def test_mark_lesson_completed_sets_status(self, async_session):
        """Existing in_progress record transitions to completed."""
        instructor = await create_test_instructor(async_session, email="i5@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 5")
        lesson = await create_test_lesson(async_session, course.id, title="L5")
        student = await create_test_user(async_session, email="s5@test.com")

        await create_test_progress(
            async_session, student["user"].id, lesson.id, status="in_progress"
        )

        service = ProgressService(async_session)
        progress = await service.mark_lesson_completed(student["user"].id, lesson.id)

        assert progress.status == ProgressStatus.COMPLETED
        assert progress.completed_at is not None

    async def test_mark_lesson_completed_creates_if_missing(self, async_session):
        """No prior record → creates a completed record."""
        instructor = await create_test_instructor(async_session, email="i6@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 6")
        lesson = await create_test_lesson(async_session, course.id, title="L6")
        student = await create_test_user(async_session, email="s6@test.com")

        service = ProgressService(async_session)
        progress = await service.mark_lesson_completed(student["user"].id, lesson.id)

        assert progress.status == ProgressStatus.COMPLETED
        assert progress.completed_at is not None


class TestGetCourseProgress:
    """Tests for ProgressService.get_course_progress()."""

    async def test_get_course_progress_partial(self, async_session):
        """2 of 3 lessons completed → 66.67% progress."""
        instructor = await create_test_instructor(async_session, email="i7@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 7")
        lesson1 = await create_test_lesson(async_session, course.id, title="L7a", order=1)
        lesson2 = await create_test_lesson(async_session, course.id, title="L7b", order=2)
        lesson3 = await create_test_lesson(async_session, course.id, title="L7c", order=3)
        student = await create_test_user(async_session, email="s7@test.com")

        await create_test_progress(
            async_session, student["user"].id, lesson1.id, status="completed"
        )
        await create_test_progress(
            async_session, student["user"].id, lesson2.id, status="completed"
        )
        await create_test_progress(
            async_session, student["user"].id, lesson3.id, status="in_progress"
        )

        service = ProgressService(async_session)
        result = await service.get_course_progress(student["user"].id, course.id)

        assert result.completed_lessons == 2
        assert result.total_lessons == 3
        assert result.percent_complete == pytest.approx(66.67)
        assert result.is_complete is False

    async def test_get_course_progress_100(self, async_session):
        """All lessons completed → is_complete=True."""
        instructor = await create_test_instructor(async_session, email="i8@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 8")
        lesson1 = await create_test_lesson(async_session, course.id, title="L8a", order=1)
        lesson2 = await create_test_lesson(async_session, course.id, title="L8b", order=2)
        student = await create_test_user(async_session, email="s8@test.com")

        await create_test_progress(
            async_session, student["user"].id, lesson1.id, status="completed"
        )
        await create_test_progress(
            async_session, student["user"].id, lesson2.id, status="completed"
        )

        service = ProgressService(async_session)
        result = await service.get_course_progress(student["user"].id, course.id)

        assert result.completed_lessons == 2
        assert result.total_lessons == 2
        assert result.percent_complete == 100.0
        assert result.is_complete is True

    async def test_get_course_progress_empty(self, async_session):
        """Course with 0 lessons → 0%, is_complete=True (vacuous truth)."""
        instructor = await create_test_instructor(async_session, email="i9@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Course 9")
        student = await create_test_user(async_session, email="s9@test.com")

        service = ProgressService(async_session)
        result = await service.get_course_progress(student["user"].id, course.id)

        assert result.total_lessons == 0
        assert result.completed_lessons == 0
        assert result.percent_complete == 0.0
        assert result.is_complete is True

    async def test_get_all_courses_progress(self, async_session):
        """get_all_courses_progress returns one entry per enrolled course."""
        instructor = await create_test_instructor(async_session, email="i10@test.com")
        course_a = await create_test_course(
            async_session, instructor["user"].id, title="Course 10a"
        )
        course_b = await create_test_course(
            async_session, instructor["user"].id, title="Course 10b"
        )
        student = await create_test_user(async_session, email="s10@test.com")

        await create_test_enrollment(async_session, student["user"].id, course_a.id)
        await create_test_enrollment(async_session, student["user"].id, course_b.id)

        service = ProgressService(async_session)
        results = await service.get_all_courses_progress(student["user"].id)

        assert len(results) == 2
        course_ids = {str(r.course_id) for r in results}
        assert str(course_a.id) in course_ids
        assert str(course_b.id) in course_ids
