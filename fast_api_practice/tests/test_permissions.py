"""Unit tests for src/core/permissions.py and role enums."""

from datetime import UTC, datetime

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
