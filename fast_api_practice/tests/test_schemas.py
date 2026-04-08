"""Tests for Pydantic schemas — validation logic only (no DB)."""

from datetime import UTC

import pytest
from pydantic import ValidationError

from src.domain.entities.project_member import ProjectMemberRole
from src.domain.entities.task import TaskPriority, TaskStatus
from src.schemas.comment import CommentCreateRequest, CommentUpdateRequest
from src.schemas.project import (
    AddMemberRequest,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    UpdateMemberRoleRequest,
)
from src.schemas.task import TaskCreateRequest, TaskUpdateRequest


class TestProjectSchemas:
    def test_create_valid(self):
        s = ProjectCreateRequest(name="My Project", description="desc")
        assert s.name == "My Project"

    def test_create_empty_name_fails(self):
        with pytest.raises(ValidationError):
            ProjectCreateRequest(name="")

    def test_create_name_too_long_fails(self):
        with pytest.raises(ValidationError):
            ProjectCreateRequest(name="x" * 101)

    def test_create_no_description(self):
        s = ProjectCreateRequest(name="Proj")
        assert s.description is None

    def test_update_all_none(self):
        s = ProjectUpdateRequest()
        assert s.name is None
        assert s.description is None

    def test_update_partial(self):
        s = ProjectUpdateRequest(name="New Name")
        assert s.name == "New Name"

    def test_add_member_defaults_to_member_role(self):
        s = AddMemberRequest(user_id=5)
        assert s.role == ProjectMemberRole.MEMBER

    def test_add_member_manager_role(self):
        s = AddMemberRequest(user_id=5, role=ProjectMemberRole.ADMIN)
        assert s.role == ProjectMemberRole.ADMIN

    def test_update_member_role_valid(self):
        s = UpdateMemberRoleRequest(role=ProjectMemberRole.ADMIN)
        assert s.role == ProjectMemberRole.ADMIN

    def test_update_member_role_invalid(self):
        with pytest.raises(ValidationError):
            UpdateMemberRoleRequest(role="owner")  # type: ignore[arg-type]


class TestTaskSchemas:
    def test_create_valid(self):
        s = TaskCreateRequest(title="Fix bug")
        assert s.title == "Fix bug"
        assert s.status == TaskStatus.TODO
        assert s.priority == TaskPriority.MEDIUM

    def test_create_empty_title_fails(self):
        with pytest.raises(ValidationError):
            TaskCreateRequest(title="")

    def test_create_title_too_long_fails(self):
        with pytest.raises(ValidationError):
            TaskCreateRequest(title="x" * 201)

    def test_create_with_all_fields(self):
        from datetime import datetime

        due = datetime(2030, 1, 1, tzinfo=UTC)
        s = TaskCreateRequest(
            title="Task",
            description="desc",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            assignee_id=3,
            due_date=due,
        )
        assert s.status == TaskStatus.IN_PROGRESS
        assert s.priority == TaskPriority.HIGH
        assert s.assignee_id == 3
        assert s.due_date == due

    def test_update_partial(self):
        s = TaskUpdateRequest(status=TaskStatus.DONE)
        assert s.status == TaskStatus.DONE
        assert s.title is None

    def test_update_empty_title_fails(self):
        with pytest.raises(ValidationError):
            TaskUpdateRequest(title="")


class TestCommentSchemas:
    def test_create_valid(self):
        s = CommentCreateRequest(content="Nice work!")
        assert s.content == "Nice work!"

    def test_create_empty_fails(self):
        with pytest.raises(ValidationError):
            CommentCreateRequest(content="")

    def test_update_valid(self):
        s = CommentUpdateRequest(content="Updated comment")
        assert s.content == "Updated comment"

    def test_update_empty_fails(self):
        with pytest.raises(ValidationError):
            CommentUpdateRequest(content="")
