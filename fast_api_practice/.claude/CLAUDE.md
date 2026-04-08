# Claude Instructions — Collaborative Task Manager API

## Project Context

- FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL 17 + Pydantic v2
- Clean architecture: API routes → Services → Repositories → DB
- Python 3.12+, tested with pytest + httpx (REST) + starlette TestClient (WebSocket)
- Linting: Ruff | Type checking: ty | Formatting: Ruff format

---

## 🚫 CRITICAL RULE: Never Use Terminal to Write Code Files

**Do NOT use shell commands (`echo`, `cat`, `tee`, `heredoc >>`) to create or edit source files.**

Reasons:
1. Long heredocs freeze the terminal on macOS zsh when the content exceeds ~4 KB.
2. Shell escaping corrupts special characters (`$`, `"`, backticks) inside Python code.
3. It bypasses the editor's undo/diff history.

**Always use the file editing tools instead:**
- `create_file` — for new files
- `insert_edit_into_file` — for inserting/replacing blocks
- `replace_string_in_file` — for targeted single-occurrence replacements

**Terminal is only for:**
- Running commands: `pytest`, `ruff check`, `uv add`, `alembic upgrade`
- Short read-only operations: `ls`, `cat <small-file>`, `grep`
- Git operations: `git status`, `git diff`

---

## Architecture Rules

| Layer | Location | Rules |
|-------|----------|-------|
| Routes | `src/api/v1/` | Thin controllers. Inject `BackgroundTasks`, fire WS notifications here. Catch domain exceptions (`LookupError`, `PermissionError`, `ValueError`) and map to `HTTPException`. |
| Services | `src/domain/services/` | Business logic only. Raise domain exceptions (`LookupError`, `PermissionError`, `ValueError`). **Never import or raise `HTTPException`.** |
| Repositories | `src/infrastructure/database/repositories.py` | DB access only. Return domain entities. Validate `update()` fields against allowlists. Validate `sort_by` against allowed columns. |
| Schemas | `src/schemas/` | Pydantic v2. All response/request models. |
| Entities | `src/domain/entities/` | Pure dataclasses/Pydantic without DB coupling. |

---

## Code Conventions

- **Logging:** Always `structlog.get_logger(__name__)`. Never `print()` or `logging.getLogger()`.
- **Background tasks:** `BackgroundTasks.add_task()` in route layer only (sync callables preferred).
- **WebSocket notifications:** `await ws_manager.send_to_user(...)` in route layer only.
- **Enum values:** Convert with `.value` before passing to `service.update_task(**updates)`.
- **Commits:** Session `commit()` must happen in `get_async_session` override in tests — match the real implementation exactly.
- **Session override in tests:** Always replicate the real `get_async_session` pattern (commit on success, rollback on exception).

---

## Test Conventions

- REST tests: `httpx.AsyncClient` + `pytest-asyncio` async fixtures in `conftest.py`
- WebSocket tests: `starlette.testclient.TestClient` with **sync `def` tests** (not `async def`)
- SQLite in-memory (`aiosqlite + StaticPool`) for WS tests — avoids event-loop conflicts with asyncpg
- **Never use `asyncio.new_event_loop()` to pre-create tables** — the tables will be invisible to TestClient's event loop. Create tables inside the lifespan or via `StaticPool` with a shared connection.
- Use `noqa: SIM117` only when a nested `with` is genuinely unavoidable (e.g. `with make_client() as tc: with tc.websocket_connect(...)`).

---

## Common Gotchas

1. **Session not committed in test override** → `get_current_user` can't find the registered user → `401` on all subsequent requests. Fix: mirror `get_async_session` exactly (commit + rollback on exception).
2. **Assignee not a project member** → task creation returns `403`. Fix: `POST /projects/{id}/members` first.
3. **`asyncio.new_event_loop()` for table creation** → tables exist in loop A, TestClient uses loop B → tables invisible → all DB calls fail. Fix: create tables inside the TestClient's lifespan.
4. **`project_id` mismatch** → always validate `task.project_id == project_id` in get/update/delete.
5. **Enum `.value` not extracted** → SQLAlchemy receives an Enum object instead of a string → `DataError`. Fix: always do `updates["status"] = updates["status"].value` before `**updates`.
6. **structlog not configured** → first log call raises. Fix: `configure_logging()` runs in `lifespan`.
7. **Terminal heredoc freeze** → never write code files via shell. Use `create_file` / `insert_edit_into_file`.

### Lessons from Supporter Code Review

8. **Services must not raise `HTTPException`** → Services are domain logic; they should raise `LookupError` (404), `PermissionError` (403), or `ValueError` (400/409). Route handlers catch these and map to `HTTPException`.
9. **Repository `update()` must validate field names** → `setattr(model, key, value)` with unchecked `**fields` bypasses type safety. Always check keys against `_ALLOWED_UPDATE_FIELDS` frozenset and raise `ValueError` for unknown keys.
10. **Repository `sort_by` must be validated** → `getattr(Model, sort_by, fallback)` silently falls back on garbage input. Validate against `_ALLOWED_SORT_FIELDS` and raise `ValueError` if invalid.
11. **Single-value enums are a code smell** → `UserRole` with only `USER` was pointless. Added `ADMIN` to make the global role meaningful alongside project-level `ProjectMemberRole.ADMIN`.
12. **Config defaults hide misconfigurations** → `DATABASE_URL` and `JWT_SECRET_KEY` should have no defaults; use `@model_validator` to raise `ValueError` if empty. `DEBUG` should default to `False` (secure by default).

---

## Running Checks

```bash
# Lint
.venv/bin/python -m ruff check .

# Type check
.venv/bin/ty check src/

# Tests (fast — WebSocket only)
.venv/bin/python -m pytest tests/test_websockets.py -v

# Full suite
.venv/bin/python -m pytest tests/ -q

# Coverage
.venv/bin/python -m pytest --cov=src --cov-report=term-missing tests/
```

---

## File Map (key files)

```
src/
├── main.py                          # FastAPI app factory, lifespan, routers
├── core/
│   ├── config.py                    # Settings (pydantic-settings)
│   ├── security.py                  # JWT encode/decode, bcrypt
│   └── permissions.py               # RBAC helpers
├── api/
│   ├── dependencies.py              # get_current_user, get_*_service
│   ├── middleware.py                # request_id, timing
│   └── v1/
│       ├── auth.py                  # register, login, refresh
│       ├── users.py                 # me, update me
│       ├── projects.py              # project CRUD + members
│       ├── tasks.py                 # task CRUD + bg email + WS notify
│       └── comments.py              # comment CRUD
├── domain/
│   ├── entities/                    # Pure domain objects
│   └── services/                    # Business logic
├── infrastructure/
│   ├── background.py                # simulate_*_email (sync, structlog only)
│   └── database/
│       ├── connection.py            # async_engine, get_async_session
│       ├── models.py                # SQLAlchemy ORM models
│       └── repositories/            # SQLAlchemy repo implementations
├── schemas/                         # Pydantic request/response models
└── websockets/
    ├── notifications.py             # ConnectionManager + manager singleton
    └── router.py                    # /ws/notifications endpoint
tests/
├── conftest.py                      # Async fixtures (httpx client, DB setup)
├── test_websockets.py               # Sync TestClient WS tests
└── test_background.py               # Background email tests
```
