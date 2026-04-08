import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import create_access_token, hash_password
from src.infrastructure.database.models import UserModel


# ── User factory ─────────────────────────────────────────────────────────────
@pytest.fixture
async def create_test_user(db_session: AsyncSession):
    """Factory: create a user, return (UserModel, plain_password)."""

    async def _create(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "password123",
    ) -> tuple[UserModel, str]:
        user = UserModel(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)
        return user, password

    return _create


@pytest.fixture
async def auth_headers(create_test_user) -> dict[str, str]:
    """Auth headers for a regular member user."""
    user, _ = await create_test_user()
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(create_test_user) -> dict[str, str]:
    """Auth headers for a second regular user (used where two users are needed)."""
    user, _ = await create_test_user(username="admin", email="admin@example.com")
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}
