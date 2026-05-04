"""
Tests for users router — API endpoint tests.

Uses httpx.AsyncClient to test the user profile endpoints
through the full FastAPI stack.
"""

from tests.conftest import create_test_user


class TestGetMeEndpoint:
    """Tests for GET /api/v1/users/me."""

    async def test_get_me_200(self, client, async_session):
        """Authenticated request returns 200 + UserResponse."""
        test_data = await create_test_user(
            async_session,
            email="getme@example.com",
            display_name="Get Me User",
        )
        response = await client.get(
            "/api/v1/users/me",
            headers=test_data["auth_header"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "getme@example.com"
        assert data["display_name"] == "Get Me User"
        assert data["role"] == "student"
        assert "id" in data
        assert "created_at" in data

    async def test_get_me_401_no_token(self, client):
        """Request without auth token returns 401."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestPatchMeEndpoint:
    """Tests for PATCH /api/v1/users/me."""

    async def test_patch_me_200(self, client, async_session):
        """Authenticated PATCH updates fields and returns 200."""
        test_data = await create_test_user(
            async_session,
            email="patchme@example.com",
            display_name="Original Name",
        )
        response = await client.patch(
            "/api/v1/users/me",
            headers=test_data["auth_header"],
            json={"display_name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"
        assert data["email"] == "patchme@example.com"  # unchanged

    async def test_patch_me_401_no_token(self, client):
        """PATCH without auth token returns 401."""
        response = await client.patch(
            "/api/v1/users/me",
            json={"display_name": "Hacker"},
        )
        assert response.status_code == 401
