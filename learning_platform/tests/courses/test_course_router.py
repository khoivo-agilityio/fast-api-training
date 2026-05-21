"""
Tests for courses router — API endpoint tests.

Uses httpx.AsyncClient to test the course endpoints through
the full FastAPI stack (middleware, dependencies, exception handlers).
"""

from tests.conftest import (
    create_test_course,
    create_test_instructor,
    create_test_user,
)


class TestCreateCourseEndpoint:
    """Tests for POST /api/v1/courses."""

    async def test_create_course_201_instructor(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        response = await client.post(
            "/api/v1/courses",
            headers=instructor["auth_header"],
            json={"title": "New Course", "description": "A great course"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Course"
        assert data["instructor_id"] == str(instructor["user"].id)

    async def test_create_course_403_student(self, client, async_session):
        student = await create_test_user(async_session, email="s@x.com", role="student")
        response = await client.post(
            "/api/v1/courses",
            headers=student["auth_header"],
            json={"title": "Nope"},
        )
        assert response.status_code == 403  # require_roles raises InsufficientPermissions (403)

    async def test_create_course_401_no_auth(self, client):
        response = await client.post(
            "/api/v1/courses",
            json={"title": "Nope"},
        )
        assert response.status_code == 401


class TestListCoursesEndpoint:
    """Tests for GET /api/v1/courses."""

    async def test_list_courses_200(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        await create_test_course(async_session, instructor["user"].id, title="C1")
        await create_test_course(async_session, instructor["user"].id, title="C2")
        response = await client.get("/api/v1/courses", headers=instructor["auth_header"])
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_list_courses_with_search(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        await create_test_course(async_session, instructor["user"].id, title="Python")
        await create_test_course(async_session, instructor["user"].id, title="Java")
        response = await client.get(
            "/api/v1/courses?search=Python", headers=instructor["auth_header"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Python"


class TestGetCourseEndpoint:
    """Tests for GET /api/v1/courses/{id}."""

    async def test_get_course_200(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        response = await client.get(
            f"/api/v1/courses/{course.id}", headers=instructor["auth_header"]
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Test Course"

    async def test_get_course_404(self, client, async_session):
        from uuid import uuid4

        instructor = await create_test_instructor(async_session)
        response = await client.get(
            f"/api/v1/courses/{uuid4()}", headers=instructor["auth_header"]
        )
        assert response.status_code == 404


class TestUpdateCourseEndpoint:
    """Tests for PATCH /api/v1/courses/{id}."""

    async def test_update_course_200_owner(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        response = await client.patch(
            f"/api/v1/courses/{course.id}",
            headers=instructor["auth_header"],
            json={"title": "Updated"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    async def test_update_course_403_non_owner(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        other = await create_test_instructor(async_session, email="other@example.com")
        response = await client.patch(
            f"/api/v1/courses/{course.id}",
            headers=other["auth_header"],
            json={"title": "Hacked"},
        )
        assert response.status_code == 403


class TestDeleteCourseEndpoint:
    """Tests for DELETE /api/v1/courses/{id}."""

    async def test_delete_course_204_admin(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        admin = await create_test_user(async_session, email="admin@x.com", role="admin")
        response = await client.delete(
            f"/api/v1/courses/{course.id}", headers=admin["auth_header"]
        )
        assert response.status_code == 204

    async def test_delete_course_403_instructor(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        response = await client.delete(
            f"/api/v1/courses/{course.id}", headers=instructor["auth_header"]
        )
        assert response.status_code == 403  # require_roles("admin") → InsufficientPermissions


class TestEnrollEndpoint:
    """Tests for POST /api/v1/courses/{id}/enroll."""

    async def test_enroll_201_student(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        student = await create_test_user(async_session, email="student@x.com", role="student")
        response = await client.post(
            f"/api/v1/courses/{course.id}/enroll",
            headers=student["auth_header"],
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(student["user"].id)
        assert data["course_id"] == str(course.id)

    async def test_enroll_409_duplicate(self, client, async_session):
        instructor = await create_test_instructor(async_session)
        course = await create_test_course(async_session, instructor["user"].id)
        student = await create_test_user(async_session, email="student@x.com", role="student")
        await client.post(
            f"/api/v1/courses/{course.id}/enroll",
            headers=student["auth_header"],
        )
        response = await client.post(
            f"/api/v1/courses/{course.id}/enroll",
            headers=student["auth_header"],
        )
        assert response.status_code == 409
