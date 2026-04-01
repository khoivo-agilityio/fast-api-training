"""Unit tests for src/core/permissions.py and role enums."""

from datetime import UTC, datetime

from src.core.permissions import require_authenticated
from src.domain.entities.project_member import ProjectMemberRole
from src.domain.entities.user import UserEntity


def _make_user() -> UserEntity:
    return UserEntity(
        id=1,
        username="tester",
        email="tester@example.com",
        hashed_password="x",
        full_name=None,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


# ── require_authenticated ─────────────────────────────────────────────────────


class TestRequireAuthenticated:
    async def test_returns_user_when_authenticated(self):
        user = _make_user()
        result = await require_authenticated(current_user=user)
        assert result is user

    async def test_returns_correct_user_id(self):
        user = _make_user()
        result = await require_authenticated(current_user=user)
        assert result.id == 1

    async def test_is_async_callable(self):
        import inspect

        assert inspect.iscoroutinefunction(require_authenticated)


# ── ProjectMemberRole ─────────────────────────────────────────────────────────


class TestProjectMemberRole:
    def test_admin_value(self):
        assert ProjectMemberRole.ADMIN.value == "admin"

    def test_member_value(self):
        assert ProjectMemberRole.MEMBER.value == "member"

    def test_only_two_values(self):
        assert len(ProjectMemberRole) == 2

    def test_no_manager_value(self):
        values = {r.value for r in ProjectMemberRole}
        assert "manager" not in values
