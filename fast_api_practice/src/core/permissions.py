"""
Role-Based Access Control (RBAC) helpers.

Hierarchy (highest → lowest):
  admin  >  manager  >  member

Rules:
- ADMIN   — can do anything across all projects/users
- MANAGER — can manage projects they own or are manager-members of
- MEMBER  — read + create tasks/comments inside their projects
"""

from fastapi import Depends, HTTPException, status

from src.api.dependencies import get_current_user
from src.domain.entities.user import UserEntity, UserRole

# ── Role hierarchy ────────────────────────────────────────────────────────────

_ROLE_RANK: dict[UserRole, int] = {
    UserRole.MEMBER: 0,
    UserRole.MANAGER: 1,
    UserRole.ADMIN: 2,
}


def has_role(user: UserEntity, minimum_role: UserRole) -> bool:
    """Return True when user's global role meets or exceeds *minimum_role*."""
    return _ROLE_RANK.get(user.role, 0) >= _ROLE_RANK[minimum_role]


# ── FastAPI dependency factories ──────────────────────────────────────────────


def require_role(minimum_role: UserRole):
    """
    Dependency factory — injects the current user and raises 403 when their
    global role is below *minimum_role*.

    Usage::

        @router.get("/admin-only")
        async def admin_view(user = Depends(require_role(UserRole.ADMIN))):
            ...
    """

    async def _dependency(
        current_user: UserEntity = Depends(get_current_user),
    ) -> UserEntity:
        if not has_role(current_user, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires '{minimum_role}' role or higher.",
            )
        return current_user

    return _dependency


# ── Convenience shorthands ────────────────────────────────────────────────────

require_admin = require_role(UserRole.ADMIN)
require_manager = require_role(UserRole.MANAGER)
require_member = require_role(UserRole.MEMBER)  # any authenticated user


def assert_is_admin(user: UserEntity) -> None:
    """Raise 403 inline (useful inside service / route logic)."""
    if not has_role(user, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
