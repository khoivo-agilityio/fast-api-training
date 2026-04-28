"""User endpoint tests — GET /users/me, PATCH /users/me."""

from httpx import AsyncClient


class TestGetMe:
    """GET /api/v1/users/me"""

    async def test_get_me_success(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@example.com"
        assert data["display_name"] == "Test User"
        assert data["role"] == "student"
        assert "id" in data
        assert "created_at" in data

    async def test_get_me_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/users/me")
        assert resp.status_code in (401, 403)  # HTTPBearer behavior varies by version

    async def test_get_me_with_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert resp.status_code == 401


class TestUpdateMe:
    """PATCH /api/v1/users/me"""

    async def test_update_display_name(self, client: AsyncClient, auth_headers):
        resp = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"display_name": "Updated Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"

    async def test_update_avatar(self, client: AsyncClient, auth_headers):
        resp = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"avatar": "https://example.com/avatar.png"},
        )
        assert resp.status_code == 200
        assert resp.json()["avatar"] == "https://example.com/avatar.png"

    async def test_update_password(self, client: AsyncClient, auth_headers):
        """After changing password, login with new password should work."""
        # Change password
        resp = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={"password": "NewPassword456!"},
        )
        assert resp.status_code == 200

        # Login with new password
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "NewPassword456!"},
        )
        assert resp.status_code == 200

    async def test_update_empty_body(self, client: AsyncClient, auth_headers):
        """Empty update should succeed without changing anything."""
        resp = await client.patch(
            "/api/v1/users/me",
            headers=auth_headers,
            json={},
        )
        assert resp.status_code == 200

    async def test_update_me_unauthorized(self, client: AsyncClient):
        resp = await client.patch(
            "/api/v1/users/me",
            json={"display_name": "Hacker"},
        )
        assert resp.status_code in (401, 403)  # HTTPBearer behavior varies by version
