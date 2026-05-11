"""
Tests for lessons router — API endpoint tests.

Uses httpx.AsyncClient to test the lesson endpoints through
the full FastAPI stack.
"""

from tests.conftest import (
    create_test_course,
    create_test_instructor,
    create_test_lesson,
    create_test_user,
)


class TestCreateLessonEndpoint:
    """Tests for POST /api/v1/courses/{course_id}/lessons."""

    async def test_create_lesson_201_instructor(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        response = await client.post(
            f"/api/v1/courses/{course.id}/lessons",
            headers=instructor["auth_header"],
            json={"title": "Lesson 1", "content": "Content here", "order": 1},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Lesson 1"
        assert data["course_id"] == str(course.id)

    async def test_create_lesson_403_wrong_instructor(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        other = await create_test_instructor(async_session, email="other@example.com")
        response = await client.post(
            f"/api/v1/courses/{course.id}/lessons",
            headers=other["auth_header"],
            json={"title": "Hacked", "content": "Nope"},
        )
        assert response.status_code == 403

    async def test_create_lesson_401_student(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        student = await create_test_user(async_session, email="student@x.com", role="student")
        response = await client.post(
            f"/api/v1/courses/{course.id}/lessons",
            headers=student["auth_header"],
            json={"title": "Nope", "content": "Nope"},
        )
        assert response.status_code == 401


class TestListLessonsEndpoint:
    """Tests for GET /api/v1/courses/{course_id}/lessons."""

    async def test_list_lessons_200(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        await create_test_lesson(async_session, course.id, title="L1", order=1)
        await create_test_lesson(async_session, course.id, title="L2", order=2)
        response = await client.get(
            f"/api/v1/courses/{course.id}/lessons",
            headers=instructor["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    async def test_list_lessons_404_course(self, client, async_session):
        from uuid import uuid4

        instructor = await create_test_instructor(async_session)
        response = await client.get(
            f"/api/v1/courses/{uuid4()}/lessons",
            headers=instructor["auth_header"],
        )
        assert response.status_code == 404


class TestGetLessonEndpoint:
    """Tests for GET /api/v1/lessons/{id}."""

    async def test_get_lesson_200(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        response = await client.get(
            f"/api/v1/lessons/{lesson.id}",
            headers=instructor["auth_header"],
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Lesson"

    async def test_get_lesson_404(self, client, async_session):
        from uuid import uuid4

        instructor = await create_test_instructor(async_session)
        response = await client.get(
            f"/api/v1/lessons/{uuid4()}",
            headers=instructor["auth_header"],
        )
        assert response.status_code == 404

    async def test_get_lesson_tracks_progress_student(self, client, async_session):
        """GET /lessons/{id} by a student creates a progress record (no-quiz → completed)."""
        from sqlalchemy import select

        from src.progress.models import Progress, ProgressStatus

        instructor = await create_test_instructor(async_session, email="tr_i@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="Track Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="Track Lesson")
        student = await create_test_user(async_session, email="tr_s@test.com")

        response = await client.get(
            f"/api/v1/lessons/{lesson.id}",
            headers=student["auth_header"],
        )

        assert response.status_code == 200

        # Verify a progress record was created
        result = await async_session.execute(
            select(Progress).where(
                Progress.user_id == student["user"].id,
                Progress.lesson_id == lesson.id,
            )
        )
        progress = result.scalar_one_or_none()
        assert progress is not None
        # No quiz in DB → auto-completed
        assert progress.status == ProgressStatus.COMPLETED


class TestUpdateLessonEndpoint:
    """Tests for PATCH /api/v1/lessons/{id}."""

    async def test_update_lesson_200(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        response = await client.patch(
            f"/api/v1/lessons/{lesson.id}",
            headers=instructor["auth_header"],
            json={"title": "Updated Lesson"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Lesson"


class TestDeleteLessonEndpoint:
    """Tests for DELETE /api/v1/lessons/{id}."""

    async def test_delete_lesson_204(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        response = await client.delete(
            f"/api/v1/lessons/{lesson.id}",
            headers=instructor["auth_header"],
        )
        assert response.status_code == 204
