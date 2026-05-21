"""
Tests for Token Blacklist — verifies DB-backed token revocation (C2 fix).

These tests verify that:
- Logout blacklists the access token (JTI stored in DB)
- Refresh rotation blacklists the old refresh token
- Blacklisted tokens are rejected with 401
"""

from httpx import AsyncClient


class TestTokenBlacklist:
    """Tests for token blacklist functionality."""

    async def test_logout_blacklists_access_token(self, client: AsyncClient):
        """After logout, the blacklisted access token is rejected."""
        # Register and get tokens
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bl_logout@test.com",
                "password": "StrongPass123!",
                "display_name": "BL Logout",
            },
        )
        assert reg.status_code == 201
        tokens = reg.json()
        auth_header = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Logout
        resp = await client.post("/api/v1/auth/logout", headers=auth_header)
        assert resp.status_code == 200

        # Old token should now be rejected
        resp2 = await client.get("/api/v1/users/me", headers=auth_header)
        assert resp2.status_code == 401

    async def test_refresh_rotation_blacklists_old_token(self, client: AsyncClient):
        """After refresh, old refresh token is blacklisted and cannot be reused."""
        # Register and get tokens
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bl_rotate@test.com",
                "password": "StrongPass123!",
                "display_name": "BL Rotate",
            },
        )
        assert reg.status_code == 201
        old_refresh = reg.json()["refresh_token"]

        # First refresh — succeeds and blacklists the old refresh token
        resp1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert resp1.status_code == 200
        new_tokens = resp1.json()
        assert "access_token" in new_tokens

        # Attempt to reuse the OLD refresh token — should be rejected
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert resp2.status_code == 401

    async def test_new_refresh_token_works_after_rotation(self, client: AsyncClient):
        """The new refresh token from rotation should work fine."""
        # Register
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bl_newrefresh@test.com",
                "password": "StrongPass123!",
                "display_name": "BL NewRefresh",
            },
        )
        assert reg.status_code == 201
        old_refresh = reg.json()["refresh_token"]

        # First refresh
        resp1 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert resp1.status_code == 200
        new_refresh = resp1.json()["refresh_token"]

        # Second refresh with NEW token — should succeed
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh},
        )
        assert resp2.status_code == 200
