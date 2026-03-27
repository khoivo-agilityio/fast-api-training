"""Unit tests for permissions — require_authenticated & ProjectMemberRole."""

from datetime import UTC, datetime

import pytest

from src.core.permissions import require_authenticated
from src.domain.entities.project_member import ProjectMemberRole
from src.domain.entities.user import UserEntity, UserRole


def _make_user(role: UserRole = UserRole.USER) -> UserEntity:
    return UserEntity(
        id=1,
        username="tester",
        email="tester@example.com",
        hashed_password="x",
        full_name=None,
        is_active=True,
        role=role,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ── require_authenticated ─────────────────────────────────────────────────────


class TestRequireAuthenticated:
    @pytest.mark.asyncio
    async def test_returns_user_when_called(self):
        user = _make_user()
        result = await require_authenticated(current_user=user)
        assert result == user
        assert result.role == UserRole.USER


# ── ProjectMemberRole ─────────────────────────────────────────────────────────


class TestProjectMemberRole:
    def test_admin_value(self):
        assert ProjectMemberRole.ADMIN == "admin"

    def test_member_value(self):
        assert ProjectMemberRole.MEMBER == "member"

    def test_has_only_two_values(self):
        assert set(ProjectMemberRole) == {"admin", "member"}


# ── UserRole ──────────────────────────────────────────────────────────────────


class TestUserRole:
    def test_user_is_only_role(self):
        assert set(UserRole) == {"user"}

    def test_default_user(self):
        user = _make_user()
        assert user.role == UserRole.USER
