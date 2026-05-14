"""
Tests for users/service.py — UserService class.

Verifies Issue #4 fix: user service is class-based with proper
async operations and domain exception handling.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.exceptions import UserNotFound
from src.users.schemas import UserUpdateRequest
from src.users.service import UserService
from tests.conftest import create_test_user


class TestUserServiceGetById:
    """Tests for UserService.get_by_id()."""

    @pytest_asyncio.fixture
    async def service(self, async_session: AsyncSession) -> UserService:
        return UserService(async_session)

    async def test_get_by_id_found(self, service, async_session):
        """Existing user ID returns the User object."""
        test_data = await create_test_user(async_session)
        user = test_data["user"]
        result = await service.get_by_id(user.id)
        assert result.id == user.id
        assert result.email == "test@example.com"

    async def test_get_by_id_not_found(self, service):
        """Non-existent user ID raises UserNotFound."""
        from uuid import uuid4

        with pytest.raises(UserNotFound):
            await service.get_by_id(uuid4())


class TestUserServiceGetByEmail:
    """Tests for UserService.get_by_email()."""

    @pytest_asyncio.fixture
    async def service(self, async_session: AsyncSession) -> UserService:
        return UserService(async_session)

    async def test_get_by_email_found(self, service, async_session):
        """Existing email returns the User object."""
        await create_test_user(async_session, email="findme@example.com")
        result = await service.get_by_email("findme@example.com")
        assert result is not None
        assert result.email == "findme@example.com"

    async def test_get_by_email_not_found(self, service):
        """Non-existent email returns None (not an exception)."""
        result = await service.get_by_email("nobody@example.com")
        assert result is None


class TestUserServiceUpdateProfile:
    """Tests for UserService.update_profile()."""

    @pytest_asyncio.fixture
    async def service(self, async_session: AsyncSession) -> UserService:
        return UserService(async_session)

    async def test_update_display_name_only(self, service, async_session):
        """Partial update — only display_name changes, email unchanged."""
        test_data = await create_test_user(
            async_session, email="update@example.com", display_name="Old Name"
        )
        user = test_data["user"]
        update_data = UserUpdateRequest(display_name="New Name")
        updated = await service.update_profile(user.id, update_data)
        assert updated.display_name == "New Name"
        assert updated.email == "update@example.com"  # unchanged

    async def test_update_nonexistent_user(self, service):
        """Updating non-existent user raises UserNotFound."""
        from uuid import uuid4

        with pytest.raises(UserNotFound):
            await service.update_profile(uuid4(), UserUpdateRequest(display_name="Ghost"))
