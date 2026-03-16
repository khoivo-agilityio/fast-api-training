"""Unit tests for TaskService.

Uses mock repositories — no database involved.
Covers:
- create_task
- get_task (success, not found, wrong owner)
- list_tasks (pagination, status filter, empty)
- update_task (field updates, wrong owner)
- delete_task (success, wrong owner)
- get_stats (counts and overdue)
- Task entity methods (mark_as_done, is_overdue)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.domain.entities.task import Task
from src.domain.services.task_service import TaskService
from src.schemas.task_schemas import (
    TaskCreate,
    TaskListResponse,
    TaskPriority,
    TaskStatsResponse,
    TaskStatus,
    TaskUpdate,
)

# ============================================================================
# HELPERS
# ============================================================================


def make_task(
    id: int = 1,
    title: str = "Test task",
    description: str | None = None,
    status: TaskStatus = TaskStatus.TODO,
    priority: TaskPriority = TaskPriority.MEDIUM,
    owner_id: int = 42,
    due_date: datetime | None = None,
) -> Task:
    """Build a Task entity for tests."""
    return Task(
        id=id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        owner_id=owner_id,
        due_date=due_date,
    )


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_task_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def task_service(mock_task_repo: MagicMock) -> TaskService:
    return TaskService(task_repository=mock_task_repo)


# ============================================================================
# CREATE TASK
# ============================================================================


class TestCreateTask:
    def test_create_task_returns_task(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        created = make_task(id=10, title="New task", owner_id=42)
        mock_task_repo.create.return_value = created

        result = task_service.create_task(TaskCreate(title="New task"), owner_id=42)

        assert result.id == 10
        assert result.title == "New task"
        mock_task_repo.create.assert_called_once()

    def test_create_task_passes_owner_id(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.create.return_value = make_task(owner_id=99)
        task_service.create_task(TaskCreate(title="Task"), owner_id=99)
        created_task: Task = mock_task_repo.create.call_args[0][0]
        assert created_task.owner_id == 99

    def test_create_task_with_all_fields(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        due = datetime(2030, 1, 1, tzinfo=UTC)
        mock_task_repo.create.return_value = make_task(
            title="High priority",
            priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS,
            due_date=due,
        )
        data = TaskCreate(
            title="High priority",
            priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS,
            due_date=due,
        )
        result = task_service.create_task(data, owner_id=1)
        assert result.priority == TaskPriority.HIGH
        assert result.status == TaskStatus.IN_PROGRESS


# ============================================================================
# GET TASK
# ============================================================================


class TestGetTask:
    def test_get_task_returns_task(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_by_id.return_value = make_task(id=5, owner_id=42)
        result = task_service.get_task(task_id=5, owner_id=42)
        assert result.id == 5

    def test_get_task_not_found_raises_value_error(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            task_service.get_task(task_id=999, owner_id=42)

    def test_get_task_wrong_owner_raises_permission_error(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_by_id.return_value = make_task(id=5, owner_id=99)
        with pytest.raises(PermissionError, match="Not authorized"):
            task_service.get_task(task_id=5, owner_id=42)


# ============================================================================
# LIST TASKS
# ============================================================================


class TestListTasks:
    def test_list_tasks_returns_task_list_response(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_all.return_value = [make_task(id=i) for i in range(1, 4)]
        mock_task_repo.count.return_value = 3

        result = task_service.list_tasks(owner_id=1, page=1, size=20)

        assert isinstance(result, TaskListResponse)
        assert result.total == 3
        assert len(result.items) == 3
        assert result.pages == 1

    def test_list_tasks_pagination_second_page(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_all.return_value = [make_task(id=3)]
        mock_task_repo.count.return_value = 3

        result = task_service.list_tasks(owner_id=1, page=2, size=2)

        assert result.page == 2
        assert result.total == 3
        assert result.size == 1
        assert result.pages == 2

    def test_list_tasks_with_status_filter(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_all.return_value = []
        mock_task_repo.count.return_value = 0

        task_service.list_tasks(owner_id=1, page=1, size=20, status=TaskStatus.DONE)

        mock_task_repo.get_all.assert_called_once_with(1, skip=0, limit=20, status=TaskStatus.DONE)

    def test_list_tasks_empty(self, task_service: TaskService, mock_task_repo: MagicMock) -> None:
        mock_task_repo.get_all.return_value = []
        mock_task_repo.count.return_value = 0

        result = task_service.list_tasks(owner_id=1)

        assert result.total == 0
        assert result.pages == 0


# ============================================================================
# UPDATE TASK
# ============================================================================


class TestUpdateTask:
    def test_update_task_title(self, task_service: TaskService, mock_task_repo: MagicMock) -> None:
        task = make_task(id=1, owner_id=42, title="Old title")
        mock_task_repo.get_by_id.return_value = task
        mock_task_repo.update.return_value = task

        result = task_service.update_task(1, TaskUpdate(title="New title"), owner_id=42)

        assert result.title == "New title"
        mock_task_repo.update.assert_called_once()

    def test_update_task_status(self, task_service: TaskService, mock_task_repo: MagicMock) -> None:
        task = make_task(id=1, owner_id=42, status=TaskStatus.TODO)
        mock_task_repo.get_by_id.return_value = task
        mock_task_repo.update.return_value = task

        result = task_service.update_task(1, TaskUpdate(status=TaskStatus.DONE), owner_id=42)

        assert result.status == TaskStatus.DONE

    def test_update_task_unset_fields_not_overwritten(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        task = make_task(id=1, owner_id=42, priority=TaskPriority.HIGH)
        mock_task_repo.get_by_id.return_value = task
        mock_task_repo.update.return_value = task

        # Only update title — priority must stay HIGH
        result = task_service.update_task(1, TaskUpdate(title="Updated"), owner_id=42)

        assert result.priority == TaskPriority.HIGH

    def test_update_task_wrong_owner_raises_permission_error(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_by_id.return_value = make_task(id=1, owner_id=99)

        with pytest.raises(PermissionError):
            task_service.update_task(1, TaskUpdate(title="X"), owner_id=42)


# ============================================================================
# DELETE TASK
# ============================================================================


class TestDeleteTask:
    def test_delete_task_success(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_by_id.return_value = make_task(id=1, owner_id=42)
        mock_task_repo.delete.return_value = True

        result = task_service.delete_task(1, owner_id=42)

        assert result is True
        mock_task_repo.delete.assert_called_once_with(1)

    def test_delete_task_not_found_raises_value_error(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            task_service.delete_task(999, owner_id=42)

    def test_delete_task_wrong_owner_raises_permission_error(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        mock_task_repo.get_by_id.return_value = make_task(id=1, owner_id=99)
        with pytest.raises(PermissionError):
            task_service.delete_task(1, owner_id=42)


# ============================================================================
# GET STATS
# ============================================================================


class TestGetStats:
    def test_get_stats_returns_stats_response(
        self, task_service: TaskService, mock_task_repo: MagicMock
    ) -> None:
        all_tasks = [
            make_task(id=1, status=TaskStatus.TODO, priority=TaskPriority.LOW),
            make_task(id=2, status=TaskStatus.TODO, priority=TaskPriority.MEDIUM),
            make_task(id=3, status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM),
            make_task(id=4, status=TaskStatus.IN_PROGRESS, priority=TaskPriority.HIGH),
            make_task(id=5, status=TaskStatus.DONE, priority=TaskPriority.HIGH),
        ]
        mock_task_repo.count.side_effect = [5, 2, 2, 1]
        mock_task_repo.get_all.return_value = all_tasks

        result = task_service.get_stats(owner_id=1)

        assert isinstance(result, TaskStatsResponse)
        assert result.total == 5
        assert result.todo == 2
        assert result.in_progress == 2
        assert result.done == 1
        assert result.by_priority["low"] == 1
        assert result.by_priority["medium"] == 2
        assert result.by_priority["high"] == 2

    def test_get_stats_empty(self, task_service: TaskService, mock_task_repo: MagicMock) -> None:
        mock_task_repo.count.side_effect = [0, 0, 0, 0]
        mock_task_repo.get_all.return_value = []

        result = task_service.get_stats(owner_id=1)

        assert result.total == 0
        assert result.overdue == 0


# ============================================================================
# TASK ENTITY METHODS
# ============================================================================


class TestTaskEntityMethods:
    def test_mark_as_done(self) -> None:
        task = make_task(status=TaskStatus.TODO)
        task.mark_as_done()
        assert task.status == TaskStatus.DONE

    def test_mark_as_in_progress(self) -> None:
        task = make_task(status=TaskStatus.TODO)
        task.mark_as_in_progress()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_is_overdue_past_due_date(self) -> None:
        task = make_task(
            status=TaskStatus.TODO,
            due_date=datetime.now(UTC) - timedelta(days=1),
        )
        assert task.is_overdue() is True

    def test_is_overdue_future_due_date(self) -> None:
        task = make_task(
            status=TaskStatus.TODO,
            due_date=datetime.now(UTC) + timedelta(days=1),
        )
        assert task.is_overdue() is False

    def test_is_overdue_no_due_date(self) -> None:
        assert make_task(due_date=None).is_overdue() is False

    def test_is_overdue_done_task_never_overdue(self) -> None:
        task = make_task(
            status=TaskStatus.DONE,
            due_date=datetime.now(UTC) - timedelta(days=5),
        )
        assert task.is_overdue() is False
