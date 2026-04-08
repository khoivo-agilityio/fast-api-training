# Copilot Instructions — Collaborative Task Manager API

## Tech Stack

- Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), PostgreSQL 17
- Alembic for migrations | PyJWT + passlib[bcrypt] for auth
- structlog for logging | pytest + httpx for testing | Ruff for linting + formatting

## Architecture

```
src/api/v1/          → Route handlers (thin controllers, catch domain exceptions → HTTPException)
src/domain/services/ → Business logic (raise LookupError / PermissionError / ValueError — NEVER HTTPException)
src/domain/repositories/ → Abstract repo interfaces
src/infrastructure/database/ → SQLAlchemy implementations (validate update fields & sort_by)
src/schemas/         → Pydantic request/response models
src/core/            → Config, security, permissions
src/websockets/      → ConnectionManager + /ws/notifications route
src/infrastructure/background.py → Email simulation (sync, log-only)
```

## Hard Rules

1. **Never write code files via terminal** (`echo`, `cat >>`, heredocs).
   - Use `create_file` / `insert_edit_into_file` / `replace_string_in_file` tools.
   - Terminal is for: `pytest`, `ruff check`, `uv add`, `alembic upgrade`, `git`.

2. All endpoints must be **async**.

3. Use `Depends()` for all dependency injection — never instantiate services/repos manually in routes.

4. **Background tasks** (`BackgroundTasks.add_task(...)`) go in the **route layer only**.

5. **WebSocket notifications** (`await manager.send_to_user(...)`) go in the **route layer only**.

6. Services raise **domain exceptions** only: `LookupError` (→ 404), `PermissionError` (→ 403), `ValueError` (→ 400/409). Route handlers catch and convert to `HTTPException`.

7. Repository `update()` methods must validate keys against `_ALLOWED_UPDATE_FIELDS` frozenset. Raise `ValueError` for unknown keys.

8. Always validate `project_id` ownership in task get/update/delete operations.

8. Extract enum `.value` before passing to `service.update_task(**updates)`.

9. Use `structlog` for all logging — never `print()` or stdlib `logging` directly.

10. Run `ruff check .` and `pytest tests/ -q` before every commit.

## Test Patterns

- **REST:** `pytest-asyncio` + `httpx.AsyncClient` + async fixtures in `conftest.py`
- **WebSocket:** `starlette.testclient.TestClient` + sync `def` tests (no `async def`)
- **WS DB:** SQLite in-memory via `aiosqlite + StaticPool` — isolated per test
- **Session override:** Must replicate `get_async_session` exactly — commit on success, rollback on error
- **Assignee setup:** Always `POST /projects/{id}/members` before assigning a user to a task

## Key Gotchas

| # | Symptom | Root Cause | Fix |
|---|---------|------------|-----|
| 1 | 401 on all REST calls in WS tests | Session override missing `commit()` | Match `get_async_session` pattern |
| 2 | 403 on task creation with assignee | Assignee not a project member | Add member first |
| 3 | Tables not found in TestClient | Tables created on different event loop | Use StaticPool; don't pre-create on separate loop |
| 4 | Terminal freeze mid-write | Large heredoc in zsh | Use file tools, not shell |
| 5 | DataError on task update | Enum not converted to `.value` | `updates["status"] = updates["status"].value` |
| 6 | Arbitrary attribute set on ORM model | `setattr` with unchecked `**fields` | Validate against `_ALLOWED_UPDATE_FIELDS` frozenset |
| 7 | Silent sort fallback on bad input | `getattr(Model, sort_by, fallback)` | Validate against `_ALLOWED_SORT_FIELDS`, raise `ValueError` |
| 8 | Service raises `HTTPException` | Couples domain to HTTP layer | Use `LookupError`/`PermissionError`/`ValueError`; map in routes |
