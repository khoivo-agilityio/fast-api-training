"""Shared test fixtures — async SQLite DB, mocked Redis, httpx client, auth helpers."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import all models to register them with Base.metadata BEFORE table creation
import src.models  # noqa: F401
from src.database import Base, get_db

# ── Async SQLite In-Memory Engine ────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionFactory() as session:
        yield session


# ── Mock Redis ───────────────────────────────────────────────────────────────

# In-memory dict to simulate Redis
_redis_store: dict[str, str] = {}


def _make_mock_redis():
    """Create a mock Redis client backed by an in-memory dict."""
    mock = AsyncMock()

    async def mock_setex(key, ttl, value):
        _redis_store[key] = value

    async def mock_get(key):
        return _redis_store.get(key)

    async def mock_exists(key):
        return 1 if key in _redis_store else 0

    async def mock_delete(key):
        _redis_store.pop(key, None)

    async def mock_ping():
        return True

    async def mock_aclose():
        pass

    mock.setex = mock_setex
    mock.get = mock_get
    mock.exists = mock_exists
    mock.delete = mock_delete
    mock.ping = mock_ping
    mock.aclose = mock_aclose
    return mock


_mock_redis_client = _make_mock_redis()


@pytest.fixture(autouse=True)
def clear_redis_store():
    """Clear the in-memory Redis store before each test."""
    _redis_store.clear()
    yield
    _redis_store.clear()


@pytest.fixture(autouse=True)
def mock_redis():
    """Patch get_redis to return our mock client."""

    async def mock_get_redis():
        return _mock_redis_client

    with patch("src.redis.get_redis", mock_get_redis):
        yield _mock_redis_client


# ── HTTP Client ──────────────────────────────────────────────────────────────


@pytest.fixture
async def client(mock_redis) -> AsyncGenerator[AsyncClient, None]:
    """Async httpx client with overridden DB dependency and mocked Redis."""
    from src.main import app

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Auth Helpers ─────────────────────────────────────────────────────────────

TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "StrongPass123!"


@pytest.fixture
async def registered_user(client: AsyncClient) -> dict:
    """Register a test user and return the response data (tokens + user info)."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "display_name": "Test User",
        },
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
async def auth_headers(registered_user: dict) -> dict[str, str]:
    """Return Authorization headers with a valid access token."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture
async def second_user_headers(client: AsyncClient) -> dict[str, str]:
    """Register a second user and return auth headers."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user2@example.com",
            "password": "AnotherPass456!",
            "display_name": "Second User",
        },
    )
    assert resp.status_code == 201
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
