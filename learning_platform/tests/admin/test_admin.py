"""
Tests for Admin module — app-level smoke tests.

Verifies that mounting SQLAdmin doesn't break the existing health check
and that the application creates without errors.
"""


class TestAppSmoke:
    """Smoke tests after SQLAdmin is mounted."""

    async def test_health_check_still_works(self, client, async_session):
        """Health endpoint returns 200 after SQLAdmin mount."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    async def test_app_starts_with_sqladmin(self, client, async_session):
        """Application starts successfully with SQLAdmin mounted (no import errors)."""
        from src.main import app

        assert app is not None

    async def test_admin_ui_login_page_accessible(self, client, async_session):
        """SQLAdmin login page is reachable (returns 200 or redirect)."""
        response = await client.get("/admin/", follow_redirects=True)
        # SQLAdmin returns 200 on the login page
        assert response.status_code == 200
