"""Unit tests for src/core/permissions.py — has_role, require_role, assert_is_admin."""

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from src.core.permissions import assert_is_admin, has_role, require_role
from src.domain.entities.user import UserEntity, UserRole


def _make_user(role: UserRole) -> UserEntity:
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


# ── has_role ──────────────────────────────────────────────────────────────────


class TestHasRole:
    def test_member_meets_member(self):
        assert has_role(_make_user(UserRole.MEMBER), UserRole.MEMBER) is True

    def test_member_fails_manager(self):
        assert has_role(_make_user(UserRole.MEMBER), UserRole.MANAGER) is False

    def test_member_fails_admin(self):
        assert has_role(_make_user(UserRole.MEMBER), UserRole.ADMIN) is False

    def test_manager_meets_member(self):
        assert has_role(_make_user(UserRole.MANAGER), UserRole.MEMBER) is True

    def test_manager_meets_manager(self):
        assert has_role(_make_user(UserRole.MANAGER), UserRole.MANAGER) is True

    def test_manager_fails_admin(self):
        assert has_role(_make_user(UserRole.MANAGER), UserRole.ADMIN) is False

    def test_admin_meets_member(self):
        assert has_role(_make_user(UserRole.ADMIN), UserRole.MEMBER) is True

    def test_admin_meets_manager(self):
        assert has_role(_make_user(UserRole.ADMIN), UserRole.MANAGER) is True

    def test_admin_meets_admin(self):
        assert has_role(_make_user(UserRole.ADMIN), UserRole.ADMIN) is True


# ── require_role ──────────────────────────────────────────────────────────────


class TestRequireRole:
    def test_returns_callable(self):
        dep = require_role(UserRole.ADMIN)
        assert callable(dep)

    @pytest.mark.asyncio
    async def test_passes_when_role_sufficient(self):
        # require_role returns the inner async _dependency function directly
        inner = require_role(UserRole.MEMBER)
        admin = _make_user(UserRole.ADMIN)
        result = await inner(current_user=admin)
        assert result == admin

    @pytest.mark.asyncio
    async def test_raises_403_when_role_insufficient(self):
        inner = require_role(UserRole.ADMIN)
        member = _make_user(UserRole.MEMBER)
        with pytest.raises(HTTPException) as exc_info:
            await inner(current_user=member)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_manager_passes_member_gate(self):
        inner = require_role(UserRole.MEMBER)
        manager = _make_user(UserRole.MANAGER)
        result = await inner(current_user=manager)
        assert result.role == UserRole.MANAGER

    @pytest.mark.asyncio
    async def test_member_fails_manager_gate(self):
        inner = require_role(UserRole.MANAGER)
        member = _make_user(UserRole.MEMBER)
        with pytest.raises(HTTPException) as exc_info:
            await inner(current_user=member)
        assert exc_info.value.status_code == 403


# ── assert_is_admin ───────────────────────────────────────────────────────────


class TestAssertIsAdmin:
    def test_admin_passes(self):
        assert_is_admin(_make_user(UserRole.ADMIN))  # no exception

    def test_manager_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            assert_is_admin(_make_user(UserRole.MANAGER))
        assert exc_info.value.status_code == 403

    def test_member_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            assert_is_admin(_make_user(UserRole.MEMBER))
        assert exc_info.value.status_code == 403
