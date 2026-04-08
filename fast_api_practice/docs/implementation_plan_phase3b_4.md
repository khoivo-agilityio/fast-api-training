# Implementation Plan — Phase 3.5–3.6 & Phase 4

> **Target executor:** AI Agent (Claude Sonnet 4.6)
> **Date:** 2025-07-14
> **Scope:** Tasks 3.5, 3.6, 4.6, 4.7 + post-implementation artifacts

---

## 0. Original Prompt & Analysis

### 0.1 Original Prompt (paraphrased)

> "Create a detailed implementation plan for the remaining work: Phase 3 tasks 3.5–3.6 and Phase 4. The plan must:
> 1. Note the original prompt in the plan for later review, with pros/cons and improvement suggestions.
> 2. Define both execution and verification steps (linting with Ruff/ty and testing with pytest).
> 3. Write detailed specs targeting AI Agent model Claude Sonnet 4.6.
> 4. Note that mistakes should be logged in `gotchas.md` and instructions updated (`.claude/CLAUDE.md` and `.github/copilot-instructions.md`).
> 5. Indicate all changes needed: DTOs, decorators, controllers, services, tests.
> 6. After implementation, create an API changelog in `docs/api/`.
> 7. Ask the user first if there are any unclear/questions/multiple choices."

### 0.2 Pros of the Prompt

| # | Pro |
|---|-----|
| 1 | Explicit about **verification** — requires both linting and testing steps, not just implementation. |
| 2 | Targets a **specific AI model** — encourages writing unambiguous, deterministic specs. |
| 3 | Requires **traceability** — the original prompt is embedded for later review. |
| 4 | Encourages **learning** — `gotchas.md` captures mistakes so they don't repeat. |
| 5 | Demands **completeness** — DTOs/controllers/services/tests must all be specified. |
| 6 | Includes **documentation deliverables** (API changelog) — often forgotten. |

### 0.3 Cons of the Prompt

| # | Con | Impact |
|---|-----|--------|
| 1 | No **acceptance criteria per task** — "done" is loosely defined. | May cause ambiguity during verification. |
| 2 | No explicit **order of execution** between tasks — are 3.5 and 3.6 independent or sequential? | Could cause merge conflicts or wasted effort. |
| 3 | Phase 4 scope is vague — "test coverage ≥ 80%" is a metric, not a task list. | Hard for an AI agent to know when to stop adding tests. |
| 4 | Missing **rollback plan** — what if WebSocket implementation breaks existing tests? | Could spiral into debugging time. |
| 5 | "Improvement suggestions" for the prompt is meta-work embedded inside the plan — mixes concerns. | Plan becomes longer than necessary. |

### 0.4 Improvement Suggestions

1. Add explicit **acceptance criteria** per task (e.g., "Task 3.5 is done when `pytest tests/test_background.py` passes and coverage delta ≥ 0").
2. Specify **execution order** explicitly (3.5 → 3.6 → 4.6 → 4.7, or parallel tracks).
3. Replace "≥ 80% coverage" with "add tests for the files touched in 3.5/3.6 until `pytest --cov` shows ≥ 80%".
4. Separate "meta-documentation" (gotchas, instruction files) into a final cleanup step.

---

## 1. Execution Order

```
3.5 Background Tasks (email simulation)
  ↓
3.6 WebSocket Notifications
  ↓
4.6 Swagger Metadata, Tags, Examples
  ↓
4.7 README, .env.example, ER Diagram, Coverage ≥ 80%
  ↓
Post: API Changelog + gotchas.md + AI instruction files
```

Each step builds on the previous one. 3.5 must be done first because 3.6 (WebSocket notifications) will follow a similar integration pattern (hook into service → fire side-effect).

---

## 2. Task 3.5 — Background Tasks (Email Simulation)

### 2.1 Requirements (from `docs/plan.md` §3.6)

- Use **FastAPI `BackgroundTasks`** to simulate email notifications.
- Trigger on:
  - **Task assigned** (new task creation with `assignee_id`, or updating `assignee_id`).
  - **Project created**.
- The "email" is simulated — just **log** the event via `structlog`.

### 2.2 New File: `src/infrastructure/background.py`

Create this module with the following functions:

```python
# src/infrastructure/background.py
import structlog

logger = structlog.get_logger(__name__)


def simulate_task_assignment_email(
    task_id: int,
    task_title: str,
    assignee_id: int,
    project_id: int,
) -> None:
    """Simulate sending email when a task is assigned."""
    logger.info(
        "email_sent",
        email_type="task_assigned",
        task_id=task_id,
        task_title=task_title,
        assignee_id=assignee_id,
        project_id=project_id,
        message=f"Simulated email: Task '{task_title}' (ID={task_id}) "
                f"assigned to user {assignee_id} in project {project_id}.",
    )


def simulate_project_created_email(
    project_id: int,
    project_name: str,
    owner_id: int,
) -> None:
    """Simulate sending email when a project is created."""
    logger.info(
        "email_sent",
        email_type="project_created",
        project_id=project_id,
        project_name=project_name,
        owner_id=owner_id,
        message=f"Simulated email: Project '{project_name}' (ID={project_id}) "
                f"created by user {owner_id}.",
    )
```

**Key design decisions:**
- Functions are **sync** (they only log) — `BackgroundTasks.add_task()` accepts sync callables.
- Logging uses `structlog` with structured key-value pairs for machine-readability.
- Functions are pure side-effect functions — no DB access, no exceptions.

### 2.3 Changes to Route Layer

#### 2.3.1 `src/api/v1/projects.py` — `create_project` endpoint

**What changes:** Add `BackgroundTasks` parameter; after creating the project, schedule `simulate_project_created_email`.

```python
# Add import
from fastapi import BackgroundTasks
from src.infrastructure.background import simulate_project_created_email

# Modify create_project signature:
async def create_project(
    body: ProjectCreateRequest,
    background_tasks: BackgroundTasks,                    # NEW
    current_user: UserEntity = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    project = await service.create_project(
        name=body.name,
        owner_id=current_user.id,
        description=body.description,
    )
    # NEW — schedule background email
    background_tasks.add_task(
        simulate_project_created_email,
        project_id=project.id,
        project_name=project.name,
        owner_id=current_user.id,
    )
    return ProjectResponse.model_validate(project)
```

#### 2.3.2 `src/api/v1/tasks.py` — `create_task` endpoint

**What changes:** Add `BackgroundTasks` parameter; if `assignee_id` is set, schedule `simulate_task_assignment_email`.

```python
# Add import
from fastapi import BackgroundTasks
from src.infrastructure.background import simulate_task_assignment_email

# Modify create_task signature:
async def create_task(
    project_id: int,
    body: TaskCreateRequest,
    background_tasks: BackgroundTasks,                    # NEW
    current_user: UserEntity = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = await service.create_task(...)
    # NEW — schedule background email if assigned
    if task.assignee_id is not None:
        background_tasks.add_task(
            simulate_task_assignment_email,
            task_id=task.id,
            task_title=task.title,
            assignee_id=task.assignee_id,
            project_id=task.project_id,
        )
    return _task_response(task)
```

#### 2.3.3 `src/api/v1/tasks.py` — `update_task` endpoint

**What changes:** Add `BackgroundTasks` parameter; if `assignee_id` changed to a non-None value, schedule email.

```python
# Modify update_task signature:
async def update_task(
    project_id: int,
    task_id: int,
    body: TaskUpdateRequest,
    background_tasks: BackgroundTasks,                    # NEW
    current_user: UserEntity = Depends(get_current_user),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    updates = body.model_dump(exclude_unset=True)
    # ... existing enum conversion ...
    task = await service.update_task(...)
    # NEW — schedule background email if assignee changed
    if "assignee_id" in updates and task.assignee_id is not None:
        background_tasks.add_task(
            simulate_task_assignment_email,
            task_id=task.id,
            task_title=task.title,
            assignee_id=task.assignee_id,
            project_id=task.project_id,
        )
    return _task_response(task)
```

### 2.4 No DTO / Schema Changes Required

Background tasks use existing entities — no new request/response schemas needed.

### 2.5 No Service Layer Changes Required

The service layer remains unchanged. Background task scheduling lives in the **route layer** because `BackgroundTasks` is a FastAPI concern, not domain logic.

### 2.6 Tests: `tests/test_background.py`

Create a new test file:

```python
# tests/test_background.py
"""Tests for background email simulation (Task 3.5)."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_triggers_background_email(
    client: AsyncClient, auth_headers: dict, caplog
):
    """POST /projects should schedule a simulated email (visible in logs)."""
    resp = await client.post(
        "/api/v1/projects",
        json={"name": "BG Test Project"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    # Background task runs inline in test client — check log output
    assert "email_sent" in caplog.text or "project_created" in caplog.text


@pytest.mark.asyncio
async def test_create_task_with_assignee_triggers_email(
    client: AsyncClient, auth_headers: dict, project_id: int, user_id: int, caplog
):
    """POST /projects/{id}/tasks with assignee_id should trigger email."""
    resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "BG Task", "assignee_id": user_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert "task_assigned" in caplog.text


@pytest.mark.asyncio
async def test_create_task_without_assignee_no_email(
    client: AsyncClient, auth_headers: dict, project_id: int, caplog
):
    """POST /projects/{id}/tasks without assignee should NOT trigger email."""
    resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "No Assignee Task"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert "task_assigned" not in caplog.text


@pytest.mark.asyncio
async def test_update_task_assignee_triggers_email(
    client: AsyncClient, auth_headers: dict, project_id: int,
    task_id: int, user_id: int, caplog
):
    """PATCH /projects/{id}/tasks/{id} changing assignee triggers email."""
    resp = await client.patch(
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        json={"assignee_id": user_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "task_assigned" in caplog.text
```

> **Note:** The test fixtures (`project_id`, `task_id`, `user_id`) should be adapted from existing `conftest.py` patterns. If `caplog` doesn't capture structlog output by default, add a structlog test configuration or assert on the response/status instead.

### 2.7 Verification Steps

1. **Lint:** `ruff check src/infrastructure/background.py src/api/v1/tasks.py src/api/v1/projects.py`
2. **Type check:** `ty check src/infrastructure/background.py src/api/v1/tasks.py src/api/v1/projects.py`
3. **Test:** `pytest tests/test_background.py -v`
4. **Regression:** `pytest tests/ -v` (all existing tests must still pass)
5. **Manual:** Start app → create a project via Swagger → check console logs for "Simulated email" message.

---

## 3. Task 3.6 — WebSocket Notifications

### 3.1 Requirements (from `docs/plan.md` §3.7)

- Implement endpoint: `GET /ws/notifications?token={jwt}`
- Notify **assigned user** when **task status changes**.
- Support **multiple connected users**.
- Handle **disconnect properly**.

### 3.2 New File: `src/websockets/notifications.py`

```python
# src/websockets/notifications.py
"""
WebSocket connection manager for real-time notifications.

Endpoint: ws://host/ws/notifications?token=<jwt>
"""
import json

import structlog
from fastapi import WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections keyed by user_id."""

    def __init__(self) -> None:
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)
        logger.info("ws_connected", user_id=user_id)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)
        logger.info("ws_disconnected", user_id=user_id)

    async def send_to_user(self, user_id: int, data: dict) -> None:
        """Send JSON message to all connections of a given user."""
        conns = self._connections.get(user_id, [])
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, data: dict) -> None:
        """Send to all connected users (utility, not required)."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, data)


# Singleton instance
manager = ConnectionManager()
```

### 3.3 New File: `src/websockets/router.py`

```python
# src/websockets/router.py
"""WebSocket route for /ws/notifications."""
import jwt as pyjwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.core.security import decode_token
from src.websockets.notifications import manager

router = APIRouter()


@router.websocket("/ws/notifications")
async def ws_notifications(
    websocket: WebSocket,
    token: str = Query(...),
) -> None:
    """
    WebSocket endpoint for real-time notifications.
    Authenticate via ?token=<jwt_access_token>.
    """
    # 1. Authenticate
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return
        user_id = int(payload["sub"])
    except (pyjwt.PyJWTError, KeyError, ValueError):
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # 2. Register connection
    await manager.connect(user_id, websocket)

    # 3. Keep alive — wait for disconnect
    try:
        while True:
            # We don't expect client messages, but must read to detect disconnect
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
```

### 3.4 Update `src/websockets/__init__.py`

```python
# src/websockets/__init__.py
from src.websockets.notifications import manager  # noqa: F401
```

### 3.5 Wire WebSocket Router in `src/main.py`

**What changes:** Import and include the WebSocket router.

```python
# In create_app(), after the REST routers:
from src.websockets.router import router as ws_router
app.include_router(ws_router)
```

### 3.6 Integration: Notify on Task Status Change

**Where:** `src/api/v1/tasks.py` — `update_task` endpoint.

**What changes:** After a successful task update, if the `status` field was changed and the task has an assignee, send a WebSocket notification to the assignee.

```python
# Add import at top of tasks.py:
from src.websockets.notifications import manager as ws_manager

# In update_task, after `task = await service.update_task(...)`:
    # NEW — WebSocket notification on status change
    if "status" in updates and task.assignee_id is not None:
        await ws_manager.send_to_user(
            task.assignee_id,
            {
                "type": "task_status_changed",
                "task_id": task.id,
                "task_title": task.title,
                "new_status": task.status.value if hasattr(task.status, 'value') else str(task.status),
                "project_id": task.project_id,
            },
        )
```

### 3.7 No DTO / Schema Changes Required

WebSocket messages are raw JSON dicts — no Pydantic schemas needed (they're not REST responses).

### 3.8 No Service Layer Changes Required

The notification is a side-effect fired from the route layer (same pattern as background tasks).

### 3.9 Tests: `tests/test_websockets.py`

```python
# tests/test_websockets.py
"""Tests for WebSocket notifications (Task 3.6)."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ws_connect_with_valid_token(client: AsyncClient, access_token: str):
    """WebSocket should accept connection with valid JWT."""
    # httpx doesn't support WebSocket natively — use starlette TestClient
    # or the async websocket test approach from the app
    from starlette.testclient import TestClient
    from src.main import app

    with TestClient(app) as tc:
        with tc.websocket_connect(f"/ws/notifications?token={access_token}") as ws:
            # Connection established successfully
            assert ws is not None


@pytest.mark.asyncio
async def test_ws_reject_invalid_token():
    """WebSocket should close with 4001 for invalid JWT."""
    from starlette.testclient import TestClient
    from src.main import app

    with TestClient(app) as tc:
        with pytest.raises(Exception):
            with tc.websocket_connect("/ws/notifications?token=bad.token.here") as ws:
                pass  # Should not reach here


@pytest.mark.asyncio
async def test_ws_receives_task_status_notification(
    client: AsyncClient, access_token: str, auth_headers: dict,
    project_id: int, task_id_with_assignee: int, assignee_token: str
):
    """Assigned user should receive notification when task status changes."""
    from starlette.testclient import TestClient
    from src.main import app

    with TestClient(app) as tc:
        with tc.websocket_connect(
            f"/ws/notifications?token={assignee_token}"
        ) as ws:
            # Update task status via REST
            tc.patch(
                f"/api/v1/projects/{project_id}/tasks/{task_id_with_assignee}",
                json={"status": "done"},
                headers=auth_headers,
            )
            # Receive notification
            data = ws.receive_json()
            assert data["type"] == "task_status_changed"
            assert data["new_status"] == "done"
```

> **Note:** WebSocket testing with `httpx.AsyncClient` is not natively supported. Tests should use Starlette's sync `TestClient` with `websocket_connect`. Adapt fixtures from `conftest.py` accordingly. If the existing test setup only uses `httpx.AsyncClient`, a separate sync `TestClient` fixture may be needed.

### 3.10 Verification Steps

1. **Lint:** `ruff check src/websockets/ src/api/v1/tasks.py src/main.py`
2. **Type check:** `ty check src/websockets/ src/api/v1/tasks.py src/main.py`
3. **Test:** `pytest tests/test_websockets.py -v`
4. **Regression:** `pytest tests/ -v`
5. **Manual:**
   - Start app with `uvicorn src.main:app --reload`
   - Connect via WebSocket client (e.g., `websocat` or browser console):
     ```
     websocat "ws://localhost:8000/ws/notifications?token=<jwt>"
     ```
   - In another terminal, update a task's status via curl/Swagger.
   - Verify notification JSON appears in WebSocket client.

---

## 4. Task 4.6 — Swagger Metadata, Tags, Examples

### 4.1 Requirements (from `docs/plan.md` §3.11)

- Customize Swagger metadata.
- Organize endpoints by tags.
- Provide example request bodies.

### 4.2 Changes to `src/main.py`

Enhance the `FastAPI()` constructor with richer metadata:

```python
app = FastAPI(
    title="Collaborative Task Manager API",
    description=(
        "A Trello/Jira-like project & task management backend API. "
        "Supports multi-user accounts, project management, task tracking, "
        "commenting, role-based permissions (RBAC), and real-time WebSocket notifications."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "Health check endpoint"},
        {"name": "Auth", "description": "Authentication — register, login, token refresh"},
        {"name": "Users", "description": "User profile management"},
        {"name": "Projects", "description": "Project CRUD and membership management"},
        {"name": "Tasks", "description": "Task CRUD, assignment, status transitions, filtering & sorting"},
        {"name": "Comments", "description": "Task comments"},
        {"name": "WebSocket", "description": "Real-time notifications via WebSocket"},
    ],
    contact={
        "name": "API Support",
    },
    license_info={
        "name": "MIT",
    },
)
```

### 4.3 Add Example Bodies to Schemas

#### `src/schemas/project.py`

```python
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["My Awesome Project"])
    description: str | None = Field(None, max_length=2000, examples=["A project for tracking tasks"])
```

#### `src/schemas/task.py`

```python
class TaskCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Implement login page"])
    description: str | None = Field(None, max_length=5000, examples=["Build the login UI with validation"])
    # ... rest unchanged, but add examples to status/priority if desired

class TaskUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200, examples=["Updated task title"])
    # ... rest unchanged
```

#### `src/schemas/user.py`

Add `examples` to relevant fields (registration, login request bodies).

#### `src/schemas/comment.py`

Add `examples` to the comment creation body.

### 4.4 Add Tags to WebSocket Router

In `src/websockets/router.py`, the `@router.websocket` decorator doesn't support `tags` directly. Instead, document it in the `openapi_tags` list above and add a comment in the router file.

### 4.5 Verification Steps

1. **Lint:** `ruff check src/main.py src/schemas/`
2. **Type check:** `ty check src/main.py src/schemas/`
3. **Regression:** `pytest tests/ -v` (schema changes shouldn't break tests)
4. **Manual:** Open Swagger UI at `http://localhost:8000/docs` → verify:
   - Tags are organized and described.
   - Example bodies appear in "Try it out".
   - API description is rich and professional.

---

## 5. Task 4.7 — README, `.env.example`, ER Diagram, Coverage ≥ 80%

### 5.1 `.env.example`

Create/update the file at project root:

```env
# .env.example — Copy to .env and fill in values

# Database
DATABASE_URL=postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice
DATABASE_URL_TEST=postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_test

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=5

# App
APP_NAME=Collaborative Task Manager
DEBUG=true
```

### 5.2 README.md

Create/update `README.md` at project root. Must include:

1. **Project title & description**
2. **Tech stack** table
3. **Architecture overview** (layers: API → Service → Repository → DB)
4. **Setup instructions:**
   - Prerequisites (Python 3.12+, PostgreSQL 17, etc.)
   - Clone & install: `pip install -e ".[dev]"` or `uv sync`
   - Copy `.env.example` to `.env`
   - Run migrations: `alembic upgrade head`
   - Start server: `uvicorn src.main:app --reload`
5. **Running tests:** `pytest --cov=src --cov-report=term-missing`
6. **Environment variables** table
7. **API documentation:** Link to `/docs` (Swagger) and `/redoc`
8. **Async vs Sync explanation** (required by `docs/plan.md` §3.5):
   - Difference between sync and async
   - When to use each
9. **Logging:** How structured logs work, how they could integrate with ELK/Datadog/etc.
10. **WebSocket usage** — how to connect to `/ws/notifications`
11. **ER Diagram** — embed image: `![ER Diagram](docs/erd.png)`

### 5.3 ER Diagram

The ER diagram should already exist at `docs/erd.png` (referenced in `docs/analysys_plan.md`). If not, generate one using a tool like `eralchemy2` or create manually from the 5 SQLAlchemy models:

- `User` ─1:N─ `Project` (owner)
- `User` ─N:N─ `Project` (via `ProjectMember`)
- `Project` ─1:N─ `Task`
- `User` ─1:N─ `Task` (assignee)
- `User` ─1:N─ `Task` (creator)
- `User` ─1:N─ `Comment` (author)
- `Task` ─1:N─ `Comment`

### 5.4 Test Coverage ≥ 80%

Run `pytest --cov=src --cov-report=term-missing` and identify uncovered lines. Focus additional tests on:

| File | Likely gaps | Test to add |
|------|-------------|-------------|
| `src/infrastructure/background.py` | New file | Covered by `test_background.py` |
| `src/websockets/notifications.py` | New file | Covered by `test_websockets.py` |
| `src/websockets/router.py` | New file | Covered by `test_websockets.py` |
| `src/api/v1/tasks.py` | Background + WS branches | Covered by new tests |
| `src/api/v1/projects.py` | Background branch | Covered by `test_background.py` |
| `src/core/security.py` | Edge cases | Add tests if needed |
| `src/api/middleware.py` | Middleware logic | Add test if needed |
| `src/infrastructure/logging/setup.py` | Config function | Add test if needed |

If coverage is still below 80% after adding the above tests, add targeted tests for the most uncovered service/repository functions.

### 5.5 Verification Steps

1. **Lint:** `ruff check .`
2. **Type check:** `ty check src/`
3. **Test + Coverage:** `pytest --cov=src --cov-report=term-missing` — assert ≥ 80%
4. **Manual:** Verify README renders correctly on GitHub; verify `.env.example` is complete.

---

## 6. Post-Implementation: API Changelog

### 6.1 Create `docs/api/CHANGELOG.md`

```markdown
# API Changelog

## [0.1.0] — 2025-XX-XX

### Added
- **Auth:** POST /api/v1/auth/register, /login, /refresh
- **Users:** GET/PATCH /api/v1/users/me
- **Projects:** Full CRUD + membership management (POST/GET/PATCH/DELETE /api/v1/projects, members endpoints)
- **Tasks:** Full CRUD + filtering/sorting/pagination (POST/GET/PATCH/DELETE /api/v1/projects/{id}/tasks)
- **Comments:** POST/GET /api/v1/tasks/{id}/comments (if nested under tasks) or /api/v1/projects/{id}/tasks/{id}/comments
- **RBAC:** Role-based permissions (Admin, Manager, Member) applied to all routes
- **Background tasks:** Simulated email notifications on task assignment and project creation
- **WebSocket:** Real-time notifications at /ws/notifications?token={jwt} for task status changes
- **Health check:** GET /health
- **Middleware:** Request ID, execution timing, CORS, structured logging (JSON)
- **Swagger:** Custom metadata, organized tags, example request bodies
```

Update the date and details after implementation is complete. Adjust comment endpoint paths to match the actual implementation.

---

## 7. Post-Implementation: Error Tracking & AI Instruction Files

### 7.1 `gotchas.md` (project root)

Create this file to log any mistakes, unexpected behaviors, or "lessons learned" encountered during implementation. Format:

```markdown
# Gotchas

Log of mistakes and lessons learned during implementation.

## Template
- **Date:** YYYY-MM-DD
- **Task:** (e.g., 3.5)
- **Issue:** What went wrong
- **Root Cause:** Why
- **Fix:** How it was resolved
- **Prevention:** How to avoid in the future

---

(Entries added during implementation)
```

### 7.2 `.claude/CLAUDE.md`

```markdown
# Claude Instructions — Collaborative Task Manager API

## Project Context
- FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 17 + Pydantic v2
- Clean architecture: API routes → Services → Repositories → DB
- All endpoints are async; all DB access uses async sessions

## Code Conventions
- Use `structlog` for all logging (not `print` or stdlib `logging` directly)
- Background tasks use FastAPI `BackgroundTasks` in route layer, NOT in services
- WebSocket notifications are fired from route layer, NOT services
- Services raise `HTTPException` directly (pragmatic choice — not pure DDD)
- Schemas live in `src/schemas/`, entities in `src/domain/entities/`
- Tests use `httpx.AsyncClient` for REST, `starlette.testclient.TestClient` for WebSocket

## Common Gotchas
- `project_id` must be validated against the task's `project_id` in get/update/delete task operations
- Enum values must be converted with `.value` before passing as kwargs to `service.update_task()`
- structlog must be configured before first use (done in lifespan)
- See `gotchas.md` for runtime issues encountered during development
```

### 7.3 `.github/copilot-instructions.md`

```markdown
# Copilot Instructions — Collaborative Task Manager API

## Tech Stack
- Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), PostgreSQL 17
- Alembic for migrations, PyJWT + passlib[bcrypt] for auth
- structlog for logging, pytest + httpx for testing, Ruff for linting

## Architecture
- `src/api/v1/` — Route handlers (thin controllers)
- `src/domain/services/` — Business logic
- `src/domain/repositories/` — Abstract repository interfaces
- `src/infrastructure/database/` — SQLAlchemy implementations
- `src/schemas/` — Pydantic request/response models
- `src/core/` — Config, security, permissions
- `src/websockets/` — WebSocket connection manager + route

## Rules
- All endpoints must be async
- Use `Depends()` for dependency injection
- Background tasks go in route layer using `BackgroundTasks`
- WebSocket notifications go in route layer using the singleton `manager`
- Services may raise `HTTPException`
- Always validate `project_id` ownership in task operations
- Run `ruff check` and `pytest` before committing
```

---

## 8. Summary: Files to Create / Modify

### New Files

| File | Purpose |
|------|---------|
| `src/infrastructure/background.py` | Email simulation functions |
| `src/websockets/notifications.py` | ConnectionManager class |
| `src/websockets/router.py` | WebSocket endpoint |
| `tests/test_background.py` | Background task tests |
| `tests/test_websockets.py` | WebSocket tests |
| `docs/api/CHANGELOG.md` | API changelog |
| `gotchas.md` | Error tracking |
| `.claude/CLAUDE.md` | Claude AI instructions |
| `.github/copilot-instructions.md` | Copilot AI instructions |
| `.env.example` | Environment template (create or update) |
| `README.md` | Project documentation (create or update) |

### Modified Files

| File | Changes |
|------|---------|
| `src/main.py` | Add WebSocket router, enhance Swagger metadata, add `openapi_tags` |
| `src/api/v1/projects.py` | Add `BackgroundTasks` to `create_project` |
| `src/api/v1/tasks.py` | Add `BackgroundTasks` to `create_task`/`update_task`, add WS notification to `update_task` |
| `src/websockets/__init__.py` | Export `manager` |
| `src/schemas/project.py` | Add `examples` to Fields |
| `src/schemas/task.py` | Add `examples` to Fields |
| `src/schemas/user.py` | Add `examples` to Fields |
| `src/schemas/comment.py` | Add `examples` to Fields |

### No Changes Needed

| File | Reason |
|------|--------|
| `src/domain/services/task_service.py` | Background/WS are route-layer concerns |
| `src/domain/services/project_service.py` | Background is route-layer concern |
| `src/api/dependencies.py` | No new dependencies needed |
| `src/core/permissions.py` | Already complete |
| `src/api/middleware.py` | Already complete |
| `src/infrastructure/logging/setup.py` | Already complete |
| `src/infrastructure/database/models.py` | No schema changes |

---

## 9. Acceptance Criteria Checklist

- [ ] **3.5:** `src/infrastructure/background.py` exists with `simulate_task_assignment_email` and `simulate_project_created_email`
- [ ] **3.5:** `create_project` route schedules background email
- [ ] **3.5:** `create_task` route schedules background email when `assignee_id` is set
- [ ] **3.5:** `update_task` route schedules background email when `assignee_id` changes
- [ ] **3.5:** `pytest tests/test_background.py` passes
- [ ] **3.6:** `src/websockets/notifications.py` exists with `ConnectionManager`
- [ ] **3.6:** `src/websockets/router.py` exists with `/ws/notifications` endpoint
- [ ] **3.6:** WebSocket authenticates via `?token=` query param
- [ ] **3.6:** `update_task` sends WS notification on status change to assignee
- [ ] **3.6:** `pytest tests/test_websockets.py` passes
- [ ] **4.6:** Swagger UI shows organized tags with descriptions
- [ ] **4.6:** Example request bodies appear in Swagger
- [ ] **4.7:** `README.md` has setup instructions, env vars, async explanation, logging explanation
- [ ] **4.7:** `.env.example` exists with all required variables
- [ ] **4.7:** ER diagram exists at `docs/erd.png`
- [ ] **4.7:** `pytest --cov=src` shows ≥ 80% coverage
- [ ] **Post:** `docs/api/CHANGELOG.md` exists and lists all endpoints
- [ ] **Post:** `gotchas.md` exists (populated during implementation)
- [ ] **Post:** `.claude/CLAUDE.md` exists
- [ ] **Post:** `.github/copilot-instructions.md` exists
- [ ] **All:** `ruff check .` passes with no errors
- [ ] **All:** All existing tests still pass (`pytest tests/ -v`)
