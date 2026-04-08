"""
Role-Based Access Control (RBAC) helpers.

All authorization is **project-level**:
  - Project ADMIN  — full control over the project (manage members, settings)
  - Project MEMBER — read + create tasks/comments inside their projects

Global user roles are flat — every signed-up user is simply a "user".
Project-level permissions are enforced in the service layer via
ProjectMemberRole checks.
"""

from fastapi import Depends

from src.api.dependencies import get_current_user
from src.domain.entities.user import UserEntity

# ── FastAPI dependency — require any authenticated user ───────────────────────


async def require_authenticated(
    current_user: UserEntity = Depends(get_current_user),
) -> UserEntity:
    """Dependency that simply ensures the caller is logged-in."""
    return current_user
