"""
Tests for Progress Router — API endpoint tests.

Uses httpx.AsyncClient to test progress endpoints through the full FastAPI stack.
"""

from uuid import uuid4

from tests.conftest import (
    create_test_course,
    create_test_enrollment,
    create_test_instructor,
    create_test_lesson,
    create_test_progress,
    create_test_user,
)


class TestGetCourseProgressEndpoint:
    """Tests for GET /api/v1/courses/{course_id}/progress."""

    async def test_get_course_progress_200(self, client, async_session):
        """Student with 1/2 lessons completed gets correct percentages."""
        instructor = await create_test_instructor(async_session, email="pi1@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="P Course 1")
        lesson1 = await create_test_lesson(async_session, course.id, title="PL1a", order=1)
        lesson2 = await create_test_lesson(async_session, course.id, title="PL1b", order=2)
        student = await create_test_user(async_session, email="ps1@test.com")

        await create_test_enrollment(async_session, student["user"].id, course.id)
        await create_test_progress(
            async_session, student["user"].id, lesson1.id, status="completed"
        )
        await create_test_progress(
            async_session, student["user"].id, lesson2.id, status="in_progress"
        )

        response = await client.get(
            f"/api/v1/courses/{course.id}/progress",
            headers=student["auth_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert data["completed_lessons"] == 1
        assert data["total_lessons"] == 2
        assert data["percent_complete"] == 50.0
        assert data["is_complete"] is False

    async def test_get_all_progress_200(self, client, async_session):
        """GET /progress returns entries for all enrolled courses."""
        instructor = await create_test_instructor(async_session, email="pi2@test.com")
        course_a = await create_test_course(
            async_session, instructor["user"].id, title="P Course 2a"
        )
        course_b = await create_test_course(
            async_session, instructor["user"].id, title="P Course 2b"
        )
        student = await create_test_user(async_session, email="ps2@test.com")

        await create_test_enrollment(async_session, student["user"].id, course_a.id)
        await create_test_enrollment(async_session, student["user"].id, course_b.id)

        response = await client.get(
            "/api/v1/progress",
            headers=student["auth_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        course_ids = {item["course_id"] for item in data}
        assert str(course_a.id) in course_ids
        assert str(course_b.id) in course_ids

    async def test_get_course_progress_401_no_auth(self, client, async_session):
        """Unauthenticated request returns 401."""
        instructor = await create_test_instructor(async_session, email="pi3@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="P Course 3")

        response = await client.get(f"/api/v1/courses/{course.id}/progress")

        assert response.status_code == 401

    async def test_get_course_progress_404_course(self, client, async_session):
        """Non-existent course ID returns 404."""
        student = await create_test_user(async_session, email="ps4@test.com")

        response = await client.get(
            f"/api/v1/courses/{uuid4()}/progress",
            headers=student["auth_header"],
        )

        assert response.status_code == 404
