"""Shared test fixtures and entity builders.

All pytest fixtures and factory helpers live here so every test module can
import from a single source of truth instead of duplicating setup code.

Usage in test files:
    from tests.fixtures import make_user, make_task          # builders
    from tests.fixtures import mock_user_repo, auth_service  # fixtures (via conftest)

Pytest auto-discovers fixtures defined in conftest.py files. Because this
module is NOT a conftest, fixtures must be explicitly re-exported through
``tests/conftest.py`` (already done) so pytest can inject them.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.security import hash_password
from src.domain.entities.task import Task
from src.domain.entities.user import User
from src.domain.services.auth_service import AuthService
from src.domain.services.task_service import TaskService
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models import Base
from src.main import app
from src.schemas.task_schemas import TaskPriority, TaskStatus

# ============================================================================
# CONSTANTS — reusable test user data
# ============================================================================

ALICE: dict[str, str] = {
    "username": "alice",
    "email": "alice@example.com",
    "password": "secret123",
    "full_name": "Alice Test",
}

BOB: dict[str, str] = {
    "username": "bob",
    "email": "bob@example.com",
    "password": "password99",
    "full_name": "Bob Test",
}

# ============================================================================
# ENTITY BUILDERS — pure helpers, no pytest involvement
# ============================================================================


def make_user(
    id: int = 1,
    username: str = "alice",
    email: str = "alice@example.com",
    hashed_password: str = "",
    is_active: bool = True,
    full_name: str | None = "Alice",
) -> User:
    """Build a User domain entity for tests (no DB required)."""
    return User(
        id=id,
        username=username,
        email=email,
        hashed_password=hashed_password or hash_password("secret123"),
        full_name=full_name,
        is_active=is_active,
    )


def make_task(
    id: int = 1,
    title: str = "Test task",
    description: str | None = None,
    status: TaskStatus = TaskStatus.TODO,
    priority: TaskPriority = TaskPriority.MEDIUM,
    owner_id: int = 42,
    due_date: datetime | None = None,
) -> Task:
    """Build a Task domain entity for tests (no DB required)."""
    return Task(
        id=id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        owner_id=owner_id,
        due_date=due_date,
    )


def make_overdue_task(**kwargs) -> Task:  # type: ignore[no-untyped-def]
    """Build a Task that is already overdue (due yesterday, not DONE)."""
    return make_task(due_date=datetime.now(UTC) - timedelta(days=1), **kwargs)


def make_future_task(**kwargs) -> Task:  # type: ignore[no-untyped-def]
    """Build a Task with a due date in the future (not overdue)."""
    return make_task(due_date=datetime.now(UTC) + timedelta(days=7), **kwargs)


# ============================================================================
# UNIT-TEST FIXTURES — mock repositories and services (no DB)
# ============================================================================


@pytest.fixture
def mock_user_repo() -> MagicMock:
    """MagicMock satisfying the UserRepository interface.

    Default behaviour:
    - ``get_by_username`` / ``get_by_email`` → None  (no existing user)
    - ``create`` → echoes the entity back unchanged
    """
    repo = MagicMock()
    repo.get_by_username.return_value = None
    repo.get_by_email.return_value = None
    repo.create.side_effect = lambda user: user
    return repo


@pytest.fixture
def mock_task_repo() -> MagicMock:
    """MagicMock satisfying the TaskRepository interface."""
    return MagicMock()


@pytest.fixture
def auth_service(mock_user_repo: MagicMock) -> AuthService:
    """AuthService wired to a mock user repository."""
    return AuthService(user_repository=mock_user_repo)


@pytest.fixture
def task_service(mock_task_repo: MagicMock) -> TaskService:
    """TaskService wired to a mock task repository."""
    return TaskService(task_repository=mock_task_repo)


# ============================================================================
# INTEGRATION FIXTURES — real in-memory SQLite + FastAPI TestClient
# ============================================================================

_TEST_DATABASE_URL = "sqlite:///:memory:"

_test_engine = create_engine(
    _TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables() -> Generator[None, None, None]:
    """Create all DB tables once per test session; drop them on teardown."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Transactional DB session — rolls back after each test for isolation."""
    connection = _test_engine.connect()
    transaction = connection.begin()
    session = _TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with the real DB dependency replaced by the test session."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── Auth helpers ──────────────────────────────────────────────────────────────


@pytest.fixture
def registered_user(client: TestClient) -> dict:  # type: ignore[type-arg]
    """Register ALICE via the API and return the UserResponse dict."""
    resp = client.post("/api/v1/auth/register", json=ALICE)
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def auth_token(client: TestClient, registered_user: dict) -> str:  # type: ignore[type-arg]
    """Log in as ALICE and return the raw JWT access-token string."""
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": ALICE["username"], "password": ALICE["password"]},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Return ``Authorization: Bearer <token>`` headers for authenticated requests."""
    return {"Authorization": f"Bearer {auth_token}"}
