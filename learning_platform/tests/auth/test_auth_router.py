"""
Tests for auth router — API endpoint tests.

Uses httpx.AsyncClient to test the auth endpoints through the full
FastAPI stack (middleware, dependencies, exception handlers).
"""


class TestRegisterEndpoint:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_success(self, client, async_session):
        """Register with valid data returns 201 + tokens."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "register@example.com",
                "password": "securepass123",
                "display_name": "Registered User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client, async_session):
        """Register with existing email returns 409."""
        payload = {
            "email": "dupe@example.com",
            "password": "securepass123",
        }
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_register_short_password(self, client):
        """Register with password < 8 chars returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "short@example.com", "password": "short"},
        )
        assert response.status_code == 422

    async def test_register_invalid_email(self, client):
        """Register with invalid email returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "securepass123"},
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, client, async_session):
        """Login with correct credentials returns 200 + tokens."""
        # First register
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "securepass123"},
        )
        # Then login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "securepass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client, async_session):
        """Login with wrong password returns 401."""
        await client.post(
            "/api/v1/auth/register",
            json={"email": "loginwrong@example.com", "password": "securepass123"},
        )
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "loginwrong@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_email(self, client):
        """Login with unknown email returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "anypassword"},
        )
        assert response.status_code == 401


class TestRefreshEndpoint:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_success(self, client, async_session):
        """Refresh with valid token returns 200 + new tokens."""
        # Register to get tokens
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={"email": "refresh@example.com", "password": "securepass123"},
        )
        refresh_token = reg_response.json()["refresh_token"]

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client):
        """Refresh with garbage token returns 401."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.valid.token"},
        )
        assert response.status_code == 401
