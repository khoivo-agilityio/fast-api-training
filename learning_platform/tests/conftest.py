"""
Shared Test Fixtures.

Provides:
- In-memory aiosqlite database (never real PostgreSQL in tests)
- Async session factory with per-test rollback
- Mocked Redis client
- httpx.AsyncClient wrapping the FastAPI app
- Auth helper to create JWT tokens for test users

IMPORTANT: Import all ORM models before create_all (see gotchas.md #3).
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import all models before create_all — gotchas.md #3
import src.models  # noqa: F401
from src.database import Base, get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create an in-memory aiosqlite engine for the test session."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a per-test async session with rollback after each test."""
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis client — never connect to real Redis in tests."""
    mock = AsyncMock()
    mock.setex = AsyncMock()
    mock.exists = AsyncMock(return_value=0)
    mock.aclose = AsyncMock()

    with (
        patch("src.redis.redis_client", mock),
        patch("src.redis.blacklist_token", AsyncMock()) as mock_blacklist,
        patch("src.redis.is_token_blacklisted", AsyncMock(return_value=False)) as mock_bl,
    ):
        yield {
            "client": mock,
            "blacklist_token": mock_blacklist,
            "is_token_blacklisted": mock_bl,
        }


@pytest_asyncio.fixture
async def client(async_session, mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """httpx.AsyncClient wrapping the FastAPI app with test DB and mocked Redis."""
    from src.main import app

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


async def create_test_user(
    session: AsyncSession,
    email: str = "test@example.com",
    password: str = "testpassword123",
    display_name: str = "Test User",
    role: str = "student",
) -> dict:
    """Create a test user directly in the database and return user data + tokens."""
    from src.auth import security
    from src.auth.jwt import create_token_pair
    from src.users.models import User

    hashed = await security.hash_password(password)
    user = User(
        email=email,
        password=hashed,
        display_name=display_name,
        role=role,
    )
    session.add(user)
    await session.flush()

    tokens = create_token_pair(str(user.id), user.role)
    return {
        "user": user,
        "tokens": tokens,
        "auth_header": {"Authorization": f"Bearer {tokens['access_token']}"},
    }
