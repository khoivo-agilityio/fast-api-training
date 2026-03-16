"""Unit tests for Pydantic schemas.

Tests cover:
- Validation rules (min/max length, required fields)
- Default values
- Enum values
- TaskStatus and TaskPriority enums
"""

import pytest
from pydantic import ValidationError

from src.schemas.task_schemas import (
    TaskCreate,
    TaskPriority,
    TaskStatus,
    TaskUpdate,
)
from src.schemas.token_schemas import Token, TokenData
from src.schemas.user_schemas import UserCreate, UserUpdate


# ============================================================================
# TASK ENUM TESTS
# ============================================================================
class TestTaskEnums:
    """Test TaskStatus and TaskPriority enums."""

    def test_task_status_values(self) -> None:
        assert TaskStatus.TODO == "todo"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.DONE == "done"

    def test_task_priority_values(self) -> None:
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"

    def test_task_status_from_string(self) -> None:
        assert TaskStatus("todo") == TaskStatus.TODO
        assert TaskStatus("in_progress") == TaskStatus.IN_PROGRESS
        assert TaskStatus("done") == TaskStatus.DONE

    def test_task_priority_from_string(self) -> None:
        assert TaskPriority("low") == TaskPriority.LOW
        assert TaskPriority("medium") == TaskPriority.MEDIUM
        assert TaskPriority("high") == TaskPriority.HIGH

    def test_invalid_status_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskStatus("invalid")

    def test_invalid_priority_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskPriority("urgent")


# ============================================================================
# USER SCHEMA TESTS
# ============================================================================
class TestUserCreate:
    """Test UserCreate schema validation."""

    def test_valid_user_create(self) -> None:
        user = UserCreate(
            username="alice",
            email="alice@example.com",
            password="secret123",
        )
        assert user.username == "alice"
        assert str(user.email) == "alice@example.com"
        assert user.full_name is None

    def test_valid_user_create_with_full_name(self) -> None:
        user = UserCreate(
            username="bob",
            email="bob@example.com",
            password="password99",
            full_name="Bob Smith",
        )
        assert user.full_name == "Bob Smith"

    def test_username_too_short(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(username="ab", email="x@x.com", password="pass1234")
        assert "username" in str(exc_info.value)

    def test_username_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(username="a" * 51, email="x@x.com", password="pass1234")

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="not-an-email", password="pass1234")

    def test_password_too_short(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="a@b.com", password="short")

    def test_password_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(username="alice", email="a@b.com", password="x" * 101)

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(username="alice")  # type: ignore[call-arg]


class TestUserUpdate:
    """Test UserUpdate schema validation."""

    def test_all_fields_optional(self) -> None:
        """UserUpdate should be valid with no fields."""
        update = UserUpdate()
        assert update.full_name is None
        assert update.email is None
        assert update.password is None

    def test_partial_update(self) -> None:
        update = UserUpdate(full_name="New Name")
        assert update.full_name == "New Name"

    def test_invalid_email_in_update(self) -> None:
        with pytest.raises(ValidationError):
            UserUpdate(email="not-valid")


# ============================================================================
# TASK SCHEMA TESTS
# ============================================================================
class TestTaskCreate:
    """Test TaskCreate schema validation."""

    def test_minimal_task(self) -> None:
        task = TaskCreate(title="My task")
        assert task.title == "My task"
        assert task.status == TaskStatus.TODO
        assert task.priority == TaskPriority.MEDIUM
        assert task.description is None
        assert task.due_date is None

    def test_full_task(self) -> None:
        from datetime import UTC, datetime

        due = datetime(2026, 12, 31, tzinfo=UTC)
        task = TaskCreate(
            title="Deploy API",
            description="Deploy to production",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            due_date=due,
        )
        assert task.title == "Deploy API"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
        assert task.due_date == due

    def test_title_required(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreate()  # type: ignore[call-arg]

    def test_title_empty_string(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreate(title="")

    def test_title_too_long(self) -> None:
        with pytest.raises(ValidationError):
            TaskCreate(title="x" * 201)


class TestTaskUpdate:
    """Test TaskUpdate schema — all fields optional."""

    def test_empty_update_is_valid(self) -> None:
        update = TaskUpdate()
        assert update.title is None
        assert update.status is None
        assert update.priority is None

    def test_single_field_update(self) -> None:
        update = TaskUpdate(title="New title")
        assert update.title == "New title"
        assert update.status is None

    def test_status_update(self) -> None:
        update = TaskUpdate(status=TaskStatus.DONE)
        assert update.status == TaskStatus.DONE

    def test_title_empty_string_invalid(self) -> None:
        with pytest.raises(ValidationError):
            TaskUpdate(title="")


# ============================================================================
# TOKEN SCHEMA TESTS
# ============================================================================
class TestTokenSchemas:
    """Test Token and TokenData schemas."""

    def test_token_defaults(self) -> None:
        token = Token(access_token="abc.def.ghi")
        assert token.access_token == "abc.def.ghi"
        assert token.token_type == "bearer"

    def test_token_data_optional_username(self) -> None:
        td = TokenData()
        assert td.username is None

    def test_token_data_with_username(self) -> None:
        td = TokenData(username="alice")
        assert td.username == "alice"
