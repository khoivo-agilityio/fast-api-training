"""Auth endpoint tests — register, login, refresh, logout, error cases."""

from httpx import AsyncClient


class TestRegister:
    """POST /api/v1/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "display_name": "New User",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_without_display_name(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "noname@example.com", "password": "SecurePass123!"},
        )
        assert resp.status_code == 201

    async def test_register_duplicate_email(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "AnotherPass123!"},
        )
        assert resp.status_code == 409
        assert resp.json()["error_code"] == "CONFLICT"

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "SecurePass123!"},
        )
        assert resp.status_code == 422


class TestLogin:
    """POST /api/v1/auth/login"""

    async def test_login_success(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "StrongPass123!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongPassword!"},
        )
        assert resp.status_code == 401
        assert resp.json()["error_code"] == "INVALID_CREDENTIALS"

    async def test_login_nonexistent_email(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "Whatever123!"},
        )
        assert resp.status_code == 401


class TestRefresh:
    """POST /api/v1/auth/refresh"""

    async def test_refresh_success(self, client: AsyncClient, registered_user):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": registered_user["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different from old ones
        assert data["access_token"] != registered_user["access_token"]

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert resp.status_code == 401

    async def test_refresh_after_token_rotation(self, client: AsyncClient, registered_user):
        """After refreshing, the old refresh token should be invalid."""
        # First refresh — succeeds
        resp1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": registered_user["refresh_token"]},
        )
        assert resp1.status_code == 200

        # Second refresh with old token — should fail (token was rotated)
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": registered_user["refresh_token"]},
        )
        assert resp2.status_code == 401


class TestLogout:
    """POST /api/v1/auth/logout"""

    async def test_logout_success(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 204

    async def test_access_after_logout(self, client: AsyncClient, auth_headers):
        """After logout, the access token should be blacklisted."""
        # Logout
        resp = await client.post("/api/v1/auth/logout", headers=auth_headers)
        assert resp.status_code == 204

        # Try to access protected endpoint
        resp = await client.get("/api/v1/users/me", headers=auth_headers)
        assert resp.status_code == 401

    async def test_logout_without_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code in (401, 403)  # HTTPBearer behavior varies by version
