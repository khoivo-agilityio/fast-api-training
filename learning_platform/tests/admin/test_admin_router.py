"""
Tests for Admin REST Router — /api/v1/admin/* endpoints.

Uses httpx.AsyncClient to test through the full FastAPI stack.
All admin endpoints require role=admin; students and instructors get 401.
"""

from uuid import uuid4

from tests.conftest import (
    create_test_admin,
    create_test_course,
    create_test_instructor,
    create_test_user,
)


class TestAdminUsers:
    """Tests for GET/PATCH/DELETE /api/v1/admin/users."""

    async def test_admin_list_users_200(self, client, async_session):
        """Admin can list all users."""
        admin = await create_test_admin(async_session)
        # Create a couple of extra users so list isn't empty
        await create_test_user(async_session, email="u1@admintest.com")
        await create_test_user(async_session, email="u2@admintest.com")

        response = await client.get(
            "/api/v1/admin/users",
            headers=admin["auth_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # admin + 2 users

    async def test_admin_get_user_200(self, client, async_session):
        """Admin can get any user by ID."""
        admin = await create_test_admin(async_session)
        student = await create_test_user(async_session, email="target@admintest.com")

        response = await client.get(
            f"/api/v1/admin/users/{student['user'].id}",
            headers=admin["auth_header"],
        )

        assert response.status_code == 200
        assert response.json()["email"] == "target@admintest.com"

    async def test_admin_update_user_200(self, client, async_session):
        """Admin can update any user's profile."""
        admin = await create_test_admin(async_session)
        student = await create_test_user(async_session, email="upd@admintest.com")

        response = await client.patch(
            f"/api/v1/admin/users/{student['user'].id}",
            headers=admin["auth_header"],
            json={"display_name": "Updated By Admin"},
        )

        assert response.status_code == 200
        assert response.json()["display_name"] == "Updated By Admin"

    async def test_admin_delete_user_204(self, client, async_session):
        """Admin can delete a user."""
        admin = await create_test_admin(async_session)
        student = await create_test_user(async_session, email="del@admintest.com")

        response = await client.delete(
            f"/api/v1/admin/users/{student['user'].id}",
            headers=admin["auth_header"],
        )

        assert response.status_code == 204

    async def test_admin_get_user_404(self, client, async_session):
        """Getting a non-existent user returns 404."""
        admin = await create_test_admin(async_session)

        response = await client.get(
            f"/api/v1/admin/users/{uuid4()}",
            headers=admin["auth_header"],
        )

        assert response.status_code == 404


class TestAdminCourses:
    """Tests for GET/PATCH/DELETE /api/v1/admin/courses."""

    async def test_admin_list_courses_200(self, client, async_session):
        """Admin can list all courses."""
        admin = await create_test_admin(async_session)
        instructor = await create_test_instructor(async_session, email="ci@admintest.com")
        await create_test_course(async_session, instructor["user"].id, title="Admin C1")
        await create_test_course(async_session, instructor["user"].id, title="Admin C2")

        response = await client.get(
            "/api/v1/admin/courses",
            headers=admin["auth_header"],
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_admin_get_course_200(self, client, async_session):
        """Admin can get any course by ID."""
        admin = await create_test_admin(async_session)
        instructor = await create_test_instructor(async_session, email="ci2@admintest.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="Admin Get C"
        )

        response = await client.get(
            f"/api/v1/admin/courses/{course.id}",
            headers=admin["auth_header"],
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Admin Get C"

    async def test_admin_update_course_200(self, client, async_session):
        """Admin can update any course, bypassing ownership check."""
        admin = await create_test_admin(async_session)
        instructor = await create_test_instructor(async_session, email="ci3@admintest.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="Admin Upd C"
        )

        response = await client.patch(
            f"/api/v1/admin/courses/{course.id}",
            headers=admin["auth_header"],
            json={"title": "Admin Updated Course"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Admin Updated Course"

    async def test_admin_delete_course_204(self, client, async_session):
        """Admin can delete any course."""
        admin = await create_test_admin(async_session)
        instructor = await create_test_instructor(async_session, email="ci4@admintest.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="Admin Del C"
        )

        response = await client.delete(
            f"/api/v1/admin/courses/{course.id}",
            headers=admin["auth_header"],
        )

        assert response.status_code == 204


class TestAdminAccessControl:
    """Tests ensuring non-admin roles cannot access admin endpoints."""

    async def test_admin_endpoints_401_student(self, client, async_session):
        """Student gets 401 on all admin endpoints."""
        student = await create_test_user(async_session, email="s_deny@admintest.com")

        response = await client.get(
            "/api/v1/admin/users",
            headers=student["auth_header"],
        )

        assert response.status_code == 401

    async def test_admin_endpoints_401_instructor(self, client, async_session):
        """Instructor gets 401 on all admin endpoints."""
        instructor = await create_test_instructor(async_session, email="i_deny@admintest.com")

        response = await client.get(
            "/api/v1/admin/users",
            headers=instructor["auth_header"],
        )

        assert response.status_code == 401

    async def test_admin_endpoints_401_no_auth(self, client, async_session):
        """Unauthenticated request gets 401."""
        response = await client.get("/api/v1/admin/users")

        assert response.status_code == 401

    async def test_admin_list_submissions_200(self, client, async_session):
        """Admin can list submissions (empty list is fine)."""
        admin = await create_test_admin(async_session, email="adm_sub@admintest.com")

        response = await client.get(
            "/api/v1/admin/submissions",
            headers=admin["auth_header"],
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_admin_list_progress_200(self, client, async_session):
        """Admin can list progress records (empty list is fine)."""
        admin = await create_test_admin(async_session, email="adm_prog@admintest.com")

        response = await client.get(
            "/api/v1/admin/progress",
            headers=admin["auth_header"],
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)
