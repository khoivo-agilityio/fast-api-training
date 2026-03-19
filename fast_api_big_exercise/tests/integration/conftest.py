"""Shared fixtures for integration tests.

Sets up:
- In-memory SQLite database (isolated per test session)
- FastAPI TestClient with DB dependency overridden
- Helper fixtures: registered user, auth token, authenticated client
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import Base
from src.main import app

# ── In-memory SQLite engine (separate from dev DB) ──────────────────────────
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables() -> None:  # type: ignore[return]
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield  # type: ignore[misc]
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Session:  # type: ignore[return]
    """Provide a transactional test DB session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session  # type: ignore[misc]

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:  # type: ignore[return]
    """Return a TestClient with the DB dependency overridden."""

    def override_get_db():  # type: ignore[return]
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c  # type: ignore[misc]
    app.dependency_overrides.clear()


# ── Auth helpers ─────────────────────────────────────────────────────────────
ALICE = {
    "username": "alice",
    "email": "alice@example.com",
    "password": "secret123",
    "full_name": "Alice Test",
}

BOB = {
    "username": "bob",
    "email": "bob@example.com",
    "password": "password99",
    "full_name": "Bob Test",
}


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    """Register Alice and return the UserResponse dict."""
    resp = client.post("/api/v1/auth/register", json=ALICE)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def auth_token(client: TestClient, registered_user: dict) -> str:
    """Log in as Alice and return the JWT access token string."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": ALICE["username"], "password": ALICE["password"]},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Return Authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}
