from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import get_settings
from src.core.security import create_access_token, hash_password
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models import Base, UserModel

settings = get_settings()

# ── Test engine — NullPool prevents connection reuse between tests ────────────
test_engine = create_async_engine(
    settings.DATABASE_URL_TEST, echo=False, poolclass=NullPool
)
TestSessionFactory = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


# ── DB setup/teardown per test ───────────────────────────────────────────────
@pytest.fixture(autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    """Drop and recreate all tables before each test using a dedicated connection."""
    async with test_engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    yield
    async with test_engine.connect() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test DB session."""
    async with TestSessionFactory() as session:
        yield session


# ── HTTP test client ─────────────────────────────────────────────────────────
@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client wired to test DB."""
    from src.main import create_app

    app = create_app()

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_async_session] = override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ── User factory ─────────────────────────────────────────────────────────────
@pytest.fixture
async def create_test_user(db_session: AsyncSession):
    """Factory: create a user, return (UserModel, plain_password)."""

    async def _create(
        username: str = "testuser",
        email: str = "test@example.com",
        password: str = "password123",
        role: str = "user",
    ) -> tuple[UserModel, str]:
        user = UserModel(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
        )
        db_session.add(user)
        await db_session.flush()
        await db_session.refresh(user)
        return user, password

    return _create


@pytest.fixture
async def auth_headers(create_test_user) -> dict[str, str]:
    """Auth headers for a regular user."""
    user, _ = await create_test_user()
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def second_auth_headers(create_test_user) -> dict[str, str]:
    """Auth headers for a second regular user."""
    user, _ = await create_test_user(username="user2", email="user2@example.com")
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}
