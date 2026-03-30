"""Tests for background email simulation (Task 3.5).

structlog does not emit to stdlib logging by default in tests, so we configure
a custom in-memory processor that captures log entries into a list, then assert
on that list.  The fixture is function-scoped so it resets between tests.
"""

from collections.abc import Generator
from typing import Any

import pytest
import structlog
from httpx import AsyncClient

# ── structlog capture helper ─────────────────────────────────────────────────


class _LogCapture:
    """Accumulates structlog events emitted during a test."""

    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []

    def __call__(
        self,
        _logger: Any,
        _method: str,
        event_dict: dict[str, Any],
    ) -> dict[str, Any]:
        self.entries.append(event_dict.copy())
        raise structlog.DropEvent  # prevent further processing / actual output


@pytest.fixture()
def log_capture() -> Generator[_LogCapture, None, None]:
    """Configure structlog to capture events into a list for the
    duration of the test."""
    capture = _LogCapture()
    # type: ignore[arg-type] — _LogCapture satisfies the processor protocol at runtime
    structlog.configure(processors=[capture])  # type: ignore[list-item]
    yield capture
    structlog.reset_defaults()


# ── helpers ──────────────────────────────────────────────────────────────────


def _has_email(capture: _LogCapture, email_type: str) -> bool:
    return any(
        e.get("event") == "email_sent" and e.get("email_type") == email_type
        for e in capture.entries
    )


# ── tests ─────────────────────────────────────────────────────────────────────


async def test_create_project_triggers_email(
    client: AsyncClient,
    auth_headers: dict,
    log_capture: _LogCapture,
) -> None:
    """POST /projects schedules a project_created email."""
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "BG Email Project"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert _has_email(
        log_capture, "project_created"
    ), f"Expected 'project_created' email log. Captured: {log_capture.entries}"


async def test_create_task_with_assignee_triggers_email(
    client: AsyncClient,
    auth_headers: dict,
    log_capture: _LogCapture,
) -> None:
    """POST /projects/{id}/tasks with assignee_id triggers task_assigned email."""
    # Create a project (log_capture already active — project_created logged here)
    proj = await client.post(
        "/api/v1/projects",
        json={"name": "BG Task Project"},
        headers=auth_headers,
    )
    assert proj.status_code == 201
    project_id = proj.json()["id"]

    # Get the current user's id to use as assignee
    me = await client.get("/api/v1/users/me", headers=auth_headers)
    uid = me.json()["id"]

    log_capture.entries.clear()  # only care about the task creation below

    resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "BG Task With Assignee", "assignee_id": uid},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert _has_email(
        log_capture, "task_assigned"
    ), f"Expected 'task_assigned' email log. Captured: {log_capture.entries}"


async def test_create_task_without_assignee_no_email(
    client: AsyncClient,
    auth_headers: dict,
    log_capture: _LogCapture,
) -> None:
    """POST /projects/{id}/tasks without assignee_id must NOT trigger email."""
    proj = await client.post(
        "/api/v1/projects",
        json={"name": "BG No-Assignee Project"},
        headers=auth_headers,
    )
    project_id = proj.json()["id"]
    log_capture.entries.clear()

    resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "BG Task No Assignee"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert not _has_email(
        log_capture, "task_assigned"
    ), f"Expected no 'task_assigned' email. Captured: {log_capture.entries}"


async def test_update_task_assignee_triggers_email(
    client: AsyncClient,
    auth_headers: dict,
    log_capture: _LogCapture,
) -> None:
    """PATCH /projects/{id}/tasks/{id} with assignee_id triggers task_assigned email."""
    proj = await client.post(
        "/api/v1/projects",
        json={"name": "BG Assign Update Project"},
        headers=auth_headers,
    )
    project_id = proj.json()["id"]

    me = await client.get("/api/v1/users/me", headers=auth_headers)
    uid = me.json()["id"]

    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Task To Assign"},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    task_id = create_resp.json()["id"]

    log_capture.entries.clear()  # only care about the patch below

    resp = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        json={"assignee_id": uid},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert _has_email(
        log_capture, "task_assigned"
    ), f"Expected 'task_assigned' email. Captured: {log_capture.entries}"


async def test_update_task_without_assignee_no_email(
    client: AsyncClient,
    auth_headers: dict,
    log_capture: _LogCapture,
) -> None:
    """PATCH that changes only the title must NOT trigger email."""
    proj = await client.post(
        "/api/v1/projects",
        json={"name": "BG Title Update Project"},
        headers=auth_headers,
    )
    project_id = proj.json()["id"]

    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Task Title Only"},
        headers=auth_headers,
    )
    task_id = create_resp.json()["id"]
    log_capture.entries.clear()

    resp = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert not _has_email(
        log_capture, "task_assigned"
    ), f"Unexpected 'task_assigned' email. Captured: {log_capture.entries}"


# async def test_register_triggers_welcome_email(
#     client: AsyncClient,
#     log_capture: _LogCapture,
# ) -> None:
#     """POST /auth/register schedules a welcome email for the new user."""
#     resp = await client.post(
#         "/api/v1/auth/register",
#         json={
#             "username": "bgwelcomeuser",
#             "email": "bgwelcome@example.com",
#             "password": "Str0ngPass!",
#             "full_name": "BG Welcome",
#         },
#     )
#     assert resp.status_code == 201
#     assert _has_email(
#         log_capture, "welcome"
#     ), f"Expected 'welcome' email log. Captured: {log_capture.entries}"
