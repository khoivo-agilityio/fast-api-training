"""Tests for WebSocket notifications (Task 3.6).

Strategy
--------
* Starlette's sync ``TestClient`` is used for all WebSocket tests because
  ``httpx.AsyncClient`` has no WebSocket support.
* ``TestClient`` spins up its own event loop in a thread, so these tests are
  plain ``def`` (not ``async def``) — mixing async fixtures with TestClient
  causes "Future attached to a different loop" errors.
* Each test calls ``_make_sync_client()`` which wires a fresh SQLite in-memory
  DB, so tests are fully isolated without touching the PostgreSQL test DB.
* JWTs are built directly with ``create_access_token`` / ``create_refresh_token``
  — no extra DB round-trip needed.
"""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.core.security import create_access_token, create_refresh_token
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models import Base
from src.websockets.notifications import manager as ws_manager

# ── app / DB factory ──────────────────────────────────────────────────────────


async def _create_tables(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _make_sync_client() -> TestClient:
    """Fresh TestClient backed by a SQLite in-memory DB.

    Using SQLite avoids sharing the asyncpg engine (created in the pytest-asyncio
    event loop) with TestClient's own thread-local event loop.
    """
    from src.main import create_app

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create_tables(engine))

    app = create_app()

    async def _override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_session] = _override
    return TestClient(app, raise_server_exceptions=True)


# ── REST helpers ──────────────────────────────────────────────────────────────


def _register(
    tc: TestClient,
    username: str,
    email: str,
    password: str = "Pass1234!",
) -> dict:
    resp = tc.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── tests ─────────────────────────────────────────────────────────────────────


def test_ws_connect_valid_token() -> None:
    """A valid access token must be accepted."""
    with _make_sync_client() as tc:
        user = _register(tc, "wsuser", "ws@example.com")
        token = create_access_token(user["id"])

        with tc.websocket_connect(f"/ws/notifications?token={token}") as ws:
            assert ws is not None


def test_ws_reject_invalid_token() -> None:
    """An invalid JWT must be rejected (WebSocketDisconnect raised)."""
    with _make_sync_client() as tc:  # noqa: SIM117  # tc needed by inner ctx
        with (
            pytest.raises(WebSocketDisconnect),
            tc.websocket_connect("/ws/notifications?token=not.a.jwt"),
        ):
            pass


def test_ws_reject_refresh_token() -> None:
    """A refresh token (type != 'access') must be rejected."""
    with _make_sync_client() as tc:
        user = _register(tc, "wsuser2", "ws2@example.com")
        refresh = create_refresh_token(user["id"])

        with (
            pytest.raises(WebSocketDisconnect),
            tc.websocket_connect(f"/ws/notifications?token={refresh}"),
        ):
            pass


def test_ws_receives_task_status_notification() -> None:
    """The assignee must receive a WS notification when task status changes."""
    with _make_sync_client() as tc:
        owner = _register(tc, "owner", "owner@example.com")
        assignee = _register(tc, "assignee", "assignee@example.com")

        owner_token = create_access_token(owner["id"])
        assignee_token = create_access_token(assignee["id"])

        proj = tc.post(
            "/api/v1/projects",
            json={"name": "WS Test Project"},
            headers=_headers(owner_token),
        )
        assert proj.status_code == 201
        project_id = proj.json()["id"]

        # Assignee must be a project member before being assigned a task
        member_resp = tc.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": assignee["id"], "role": "member"},
            headers=_headers(owner_token),
        )
        assert member_resp.status_code == 201

        task = tc.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "WS Task", "assignee_id": assignee["id"]},
            headers=_headers(owner_token),
        )
        assert task.status_code == 201
        task_id = task.json()["id"]

        with tc.websocket_connect(f"/ws/notifications?token={assignee_token}") as ws:
            patch = tc.patch(
                f"/api/v1/projects/{project_id}/tasks/{task_id}",
                json={"status": "in_progress"},
                headers=_headers(owner_token),
            )
            assert patch.status_code == 200
            data = ws.receive_json()

        assert data["type"] == "task_status_changed"
        assert data["task_id"] == task_id
        assert data["new_status"] == "in_progress"
        assert data["project_id"] == project_id


def test_ws_no_notification_when_no_assignee() -> None:
    """A status update on an unassigned task must NOT push any WS message."""
    with _make_sync_client() as tc:
        user = _register(tc, "solo", "solo@example.com")
        token = create_access_token(user["id"])
        headers = _headers(token)

        proj = tc.post(
            "/api/v1/projects",
            json={"name": "Solo Project"},
            headers=headers,
        )
        project_id = proj.json()["id"]

        task = tc.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Unassigned Task"},
            headers=headers,
        )
        task_id = task.json()["id"]

        assert ws_manager.active_user_ids == []

        patch = tc.patch(
            f"/api/v1/projects/{project_id}/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=headers,
        )
        assert patch.status_code == 200
        assert ws_manager.active_user_ids == []
