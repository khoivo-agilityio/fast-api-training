# Gotchas

Log of mistakes and lessons learned during implementation of Phase 3.5–4.7.

---

## 2025-07-14 · Task 3.5 — Background Tasks

### macOS SSL Certificate Error on SMTP

- **Issue:** `ssl.SSLCertVerificationError: certificate verify failed` when `_send_email()` tried to connect via SMTP on macOS.
- **Root Cause:** macOS Python doesn't use the system CA store by default — `ssl.create_default_context()` finds no certificates.
- **Fix:** Added `certifi` as a dependency and passed `cafile=certifi.where()` to `ssl.create_default_context()`.
- **Prevention:** Any new SMTP / HTTPS client code on macOS must use `certifi` explicitly.

---

## 2025-07-14 · Task 3.6 — WebSocket Tests

### Session Override Missing `commit()` → `401` on All REST Calls

- **Issue:** `POST /api/v1/projects` returned `401 Unauthorized` inside `_make_sync_client()` even though `POST /api/v1/auth/register` returned `201`.
- **Root Cause:** The test's `_override` dependency for `get_async_session` was:
  ```python
  async def _override():
      async with factory() as session:
          yield session  # ← no commit!
  ```
  Without `await session.commit()`, the newly registered user was never persisted. The next request's `get_current_user` called `repo.get_by_id(user_id)` and found nothing → `401`.
- **Fix:** Mirror the real `get_async_session` exactly:
  ```python
  async def _override():
      async with factory() as session:
          try:
              yield session
              await session.commit()
          except Exception:
              await session.rollback()
              raise
  ```
- **Prevention:** All session overrides in tests **must** replicate the commit/rollback pattern of the real dependency.

### Pre-creating Tables on a Separate Event Loop

- **Issue:** `asyncio.new_event_loop().run_until_complete(_create_tables(engine))` was used to set up the SQLite schema before `TestClient` started. It appeared to work but caused subtle failures.
- **Root Cause:** `aiosqlite` runs in a background thread. The connection created during `_create_tables` is associated with loop A. `TestClient` uses its own loop B. With `StaticPool`, the same underlying `sqlite3.Connection` is reused — but the `aiosqlite` wrapper is per-loop, so the connection seen by loop B had no tables.
- **Fix:** Let `_create_tables` run on the same loop that `TestClient` will use. The simplest approach is to keep `asyncio.new_event_loop()` but ensure the `StaticPool` forces the same raw `sqlite3.Connection`. In practice this was resolved alongside the missing-commit fix, since the table DDL and DML now run in the same connection.
- **Prevention:** Never use a throw-away event loop to initialize shared state that async code in `TestClient` will depend on.

### Assignee Not a Project Member → `403` on Task Creation

- **Issue:** `POST /api/v1/projects/{id}/tasks` with `assignee_id` returned `403 Forbidden`.
- **Root Cause:** The task service validates that the assignee is a project member. The test registered the assignee but never added them to the project.
- **Fix:** Insert `POST /api/v1/projects/{id}/members` with `{"user_id": assignee_id, "role": "member"}` before creating the task.
- **Prevention:** Always add all users to the project before referencing them in task operations.

### Terminal Freeze on Large Heredoc

- **Issue:** Using `cat << 'EOF' > file.py` in zsh to write a ~200-line Python file caused the terminal to hang indefinitely.
- **Root Cause:** macOS zsh's PTY buffer overflows with large heredoc content, freezing the session.
- **Fix:** Use `create_file` / `insert_edit_into_file` tools — they write directly to disk without going through the shell PTY.
- **Prevention:** **Never use shell commands to write code files.** Terminal is only for running commands (`pytest`, `ruff`, `git`, etc.).

### `SIM117` Ruff Warning on Nested `with` in Tests

- **Issue:** `ruff check` flagged `with _make_sync_client() as tc: / with pytest.raises(...)` as nested `with` statements (SIM117).
- **Root Cause:** Ruff's SIM117 rule wants all contexts merged into one `with A, B:` — but `tc` from the outer `with` is required by the inner one, so they cannot actually be merged.
- **Fix:** Add `# noqa: SIM117` to the outer `with` line.
- **Prevention:** This pattern is unavoidable for WebSocket tests. The `noqa` comment is correct.

---

## 2026-04-02 · Server Startup

### `Could not import module "main"` When Running Uvicorn from Project Root

- **Issue:** Running `uv run uvicorn main:app --reload` from the project root fails with `ModuleNotFoundError: Could not import module "main"`.
- **Root Cause:** The application entry point is `src/main.py`, not `main.py` at the repo root. All internal imports use the `src.` prefix (e.g. `from src.api.middleware import …`), which requires the module path to include the package name.
- **Fix:** Always run from the project root using the full dotted module path:
  ```bash
  uv run uvicorn src.main:app --reload
  ```
- **Prevention:** The `README.md` "Getting Started" section documents the correct command. Never omit the `src.` prefix.
