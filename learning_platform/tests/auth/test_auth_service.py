"""
Tests for auth/service.py — AuthService class.

Verifies Issue #3 fix: auth service is class-based with proper
async bcrypt integration and domain exception handling.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.exceptions import EmailAlreadyRegistered, InvalidCredentials
from src.auth.schemas import RegisterRequest
from src.auth.service import AuthService
from tests.conftest import create_test_user


class TestAuthServiceRegister:
    """Tests for AuthService.register()."""

    @pytest_asyncio.fixture
    async def service(self, async_session: AsyncSession) -> AuthService:
        return AuthService(async_session)

    async def test_register_success(self, service: AuthService, async_session):
        """Register with valid data returns TokenResponse."""
        data = RegisterRequest(
            email="newuser@example.com",
            password="securepass123",
            display_name="New User",
        )
        result = await service.register(data)
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    async def test_register_duplicate_email(self, service: AuthService, async_session):
        """Register with existing email raises EmailAlreadyRegistered."""
        data = RegisterRequest(
            email="duplicate@example.com",
            password="securepass123",
        )
        await service.register(data)

        with pytest.raises(EmailAlreadyRegistered):
            await service.register(data)


class TestAuthServiceLogin:
    """Tests for AuthService.login()."""

    @pytest_asyncio.fixture
    async def service_with_user(self, async_session: AsyncSession):
        """Create an AuthService with a pre-existing test user."""
        service = AuthService(async_session)
        test_data = await create_test_user(
            async_session,
            email="loginuser@example.com",
            password="correctpass123",
        )
        return service, test_data

    async def test_login_success(self, service_with_user):
        """Login with correct credentials returns TokenResponse."""
        service, _ = service_with_user
        result = await service.login("loginuser@example.com", "correctpass123")
        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    async def test_login_wrong_password(self, service_with_user):
        """Login with wrong password raises InvalidCredentials."""
        service, _ = service_with_user
        with pytest.raises(InvalidCredentials):
            await service.login("loginuser@example.com", "wrongpassword")

    async def test_login_nonexistent_email(self, service_with_user):
        """Login with unknown email raises InvalidCredentials."""
        service, _ = service_with_user
        with pytest.raises(InvalidCredentials):
            await service.login("nobody@example.com", "anypassword")
