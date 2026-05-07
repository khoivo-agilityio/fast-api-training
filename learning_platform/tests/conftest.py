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


async def create_test_instructor(
    session: AsyncSession,
    email: str = "instructor@example.com",
    display_name: str = "Test Instructor",
) -> dict:
    """Create a test user with instructor role and return user data + tokens."""
    return await create_test_user(
        session, email=email, display_name=display_name, role="instructor"
    )


async def create_test_admin(
    session: AsyncSession,
    email: str = "admin@example.com",
    display_name: str = "Test Admin",
) -> dict:
    """Create a test user with admin role and return user data + tokens."""
    return await create_test_user(
        session, email=email, display_name=display_name, role="admin"
    )


async def create_test_course(
    session: AsyncSession,
    instructor_id,
    title: str = "Test Course",
    description: str | None = "A test course",
):
    """Create a test course directly in the database."""
    from src.courses.models import Course

    course = Course(title=title, instructor_id=instructor_id, description=description)
    session.add(course)
    await session.flush()
    return course


async def create_test_enrollment(session: AsyncSession, user_id, course_id):
    """Create a test enrollment directly in the database."""
    from src.courses.models import Enrollment

    enrollment = Enrollment(user_id=user_id, course_id=course_id)
    session.add(enrollment)
    await session.flush()
    return enrollment


async def create_test_lesson(
    session: AsyncSession,
    course_id,
    title: str = "Test Lesson",
    content: str = "Lesson content here.",
    order: int = 1,
):
    """Create a test lesson directly in the database."""
    from src.lessons.models import Lesson

    lesson = Lesson(
        course_id=course_id, title=title, content=content, order=order
    )
    session.add(lesson)
    await session.flush()
    return lesson


async def create_test_progress(
    session: AsyncSession,
    user_id,
    lesson_id,
    status: str = "in_progress",
):
    """Create a test progress record directly in the database."""
    from src.progress.models import Progress

    progress = Progress(user_id=user_id, lesson_id=lesson_id, status=status)
    session.add(progress)
    await session.flush()
    return progress


async def create_test_quiz(
    session: AsyncSession,
    lesson_id,
    title: str = "Test Quiz",
    description: str | None = None,
    time_limit_minutes: int | None = None,
):
    """Create a test quiz directly in the database."""
    from src.quizzes.models import Quiz

    quiz = Quiz(
        lesson_id=lesson_id,
        title=title,
        description=description,
        time_limit_minutes=time_limit_minutes,
    )
    session.add(quiz)
    await session.flush()
    return quiz


async def create_test_question(
    session: AsyncSession,
    quiz_id,
    text: str = "What is 2+2?",
    q_type: str = "mcq",
    options: list[str] | None = None,
    correct_answer: str = "4",
):
    """Create a test question directly in the database."""
    from src.quizzes.models import Question

    if options is None:
        options = ["1", "2", "3", "4"]
    question = Question(
        quiz_id=quiz_id,
        text=text,
        type=q_type,
        options=options,
        correct_answer=correct_answer,
    )
    session.add(question)
    await session.flush()
    return question

