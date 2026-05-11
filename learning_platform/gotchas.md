# Gotchas — Learning Platform

> Living document. Add new entries at the top.

---

## 17. Helper vs. Utils vs. Service vs. DI Factory — where does my function go?

**Problem**: It's easy to dump everything into `service.py` or create a grab-bag
`utils.py`. Knowing the right home prevents duplication and misplaced logic.

### Decision flowchart

```
Does the function touch the DB or orchestrate a workflow?
│
├─ YES → Service  (service.py — class with AsyncSession)
│
└─ NO (pure function)
        │
        ├─ Only used by ONE class?
        │       └─ Private @staticmethod on that class  (_grade_answer, _compute_score)
        │
        ├─ Used by MULTIPLE modules?
        │       └─ Standalone module  (auth/jwt.py, auth/security.py, pagination.py)
        │
        └─ Wires a FastAPI request lifecycle?
                └─ Depends() factory  (dependencies.py — get_current_user, require_roles)
```

### The four kinds in this codebase

| Kind | Location | DB session | Domain knowledge | Example |
|------|----------|-----------|-----------------|---------|
| **Service** | `feature/service.py` | ✅ required | ✅ yes | `SubmissionService.submit()` |
| **Private helper** | `@staticmethod` on service | ❌ never | ✅ yes (scoring rules) | `SubmissionService._grade_answer()` |
| **Shared utility** | standalone module | ❌ never | ❌ generic | `create_access_token()`, `hash_password()` |
| **DI factory** | `feature/dependencies.py` | yields it | ❌ generic | `get_current_user()`, `require_roles()` |

### Rules of thumb

- **Private helper** → extract from an `async def` when the logic is pure and
  re-used within the same class. Prefix with `_`. Still testable:
  `SubmissionService._grade_answer(...)` needs no DB session.
- **Shared utility** → promote a private helper to a standalone module **only**
  when a second consumer appears. Don't pre-abstract.
- **Never put business logic in a DI factory** — it belongs in the service.
- **Never put DB calls in a utility** — move them to the service layer.

*Source: grading refactor, Phase 5*

---

## 16. SQLAdmin FK dropdowns show `<Model object at 0x...>` without `__str__`


**Symptom**: Relationship dropdowns in the SQLAdmin create/edit form display raw Python
object repr like `<src.lessons.models.Lesson object at 0x10db0bd50>` instead of a
human-readable label.

**Root cause**: SQLAdmin calls `str(obj)` to build dropdown option labels. Without a
`__str__` method, Python falls back to the default `object.__repr__`, which shows the
class path and memory address.

**Fix**: Add `__str__` to every ORM model that is referenced as a relationship in
SQLAdmin views:

```python
class Lesson(Base):
    ...
    def __str__(self) -> str:
        return self.title          # use the most descriptive field

class User(Base):
    ...
    def __str__(self) -> str:
        return f"{self.display_name} <{self.email}>"

class Question(Base):
    ...
    def __str__(self) -> str:
        return self.text[:60] + ("..." if len(self.text) > 60 else "")
```

**Rule of thumb**: Any model used in `form_columns` as a relationship attribute needs
`__str__`. Pick the most human-readable field — typically `title`, `name`, or `email`.
Truncate long text fields to ~60 chars to keep the dropdown readable.

*Source: Phase 5 SQLAdmin integration*

---

## 15. `SessionMiddleware` requires `itsdangerous` — not included transitively by sqladmin

**Symptom**: `ModuleNotFoundError: No module named 'itsdangerous'` at startup after
adding `starlette.middleware.sessions.SessionMiddleware`.

**Root cause**: `sqladmin` depends on `starlette` which ships `SessionMiddleware`, but
`itsdangerous` (which `SessionMiddleware` uses to sign cookies) is only a soft/optional
dependency of starlette. It is NOT pulled in transitively by sqladmin.

**Fix**: Add it explicitly:
```bash
uv add itsdangerous
```

*Source: Phase 5 implementation*

---

## 14. `onupdate=func.now()` causes `MissingGreenlet` in aiosqlite tests

**Symptom**: `MissingGreenlet: greenlet_spawn has not been called` when
Pydantic's `model_validate()` reads `updated_at` after an update in tests.

**Root cause**: SQLAlchemy's `onupdate` triggers a server-side refresh that
requires a greenlet context. aiosqlite doesn't handle this correctly.

**Fix**: Explicitly set `updated_at = datetime.now(UTC)` in the service layer's
update methods instead of relying on `onupdate`. Keep `onupdate` on the column
for PostgreSQL production use, but always set it explicitly in Python.

---

## 5. Railway `startCommand` runs WITHOUT a shell — inline env vars and `&&` break

**Symptom**: `The executable 'pythonunbuffered=1' could not be found.`

**Root cause**: Railway tokenizes `startCommand` and execs the first token as the
binary directly (no shell interpretation). `KEY=VALUE` prefix, `&&`, `||`, pipes,
`${VAR:-default}` are all shell features that won't work.

**Fix**:
1. Move env vars to `Dockerfile` `ENV` directive (preferred):
   ```dockerfile
   ENV PYTHONUNBUFFERED=1
   ```
2. If shell features are needed, wrap in `bash -c`:
   ```toml
   startCommand = "bash -c 'python -m alembic upgrade head && exec python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}'"
   ```
   Use `exec` before uvicorn so it replaces the bash process (PID 1 stays correct).

*Source: fast_api_practice*

---

## 6. `uvicorn`/`alembic` venv scripts have broken shebangs in multi-stage Docker builds

**Symptom**: `cannot execute: required file not found` when running
`/app/.venv/bin/uvicorn` or `/app/.venv/bin/alembic` in a Docker runtime stage.

**Root cause**: `uv sync` in the builder stage writes shebangs pointing to the
builder's Python path (`/root/.local/share/uv/python/…` or `/build/…`). That path
doesn't exist in the runtime stage.

**Fix**: **Never call bare venv scripts inside Docker.** Always use:
```bash
python -m uvicorn src.main:app ...
python -m alembic upgrade head
```
Also set `UV_PYTHON_PREFERENCE=only-system` in the builder stage.

*Source: fast_api_practice*

---

## 7. `ALTER TYPE ADD VALUE` in PostgreSQL cannot be used in same transaction as DML

**Symptom**: `asyncpg.exceptions.UnsafeNewEnumValueUsageError: unsafe use of new value`

**Root cause**: PostgreSQL requires `ALTER TYPE … ADD VALUE` to be fully committed
before any DML can reference the new enum value. Alembic wraps all steps in a single
transaction.

**Fix**: In migration, explicitly COMMIT after ADD VALUE, then BEGIN a new transaction:
```python
bind = op.get_bind()
bind.execute(sa_text("COMMIT"))
bind.execute(sa_text("ALTER TYPE my_enum ADD VALUE IF NOT EXISTS 'new_val'"))
bind.execute(sa_text("COMMIT"))
bind.execute(sa_text("BEGIN"))
op.execute("UPDATE my_table SET col = 'new_val' WHERE ...")
```

*Source: fast_api_practice*

---

## 8. Multiple Alembic heads crash container startup

**Symptom**: `FAILED: Multiple head revisions are present for given argument 'head'`

**Root cause**: Two migration files with the same parent revision create a branch.

**Fix**: Identify the duplicate with `uv run alembic heads`, delete the stale file.
If both are real divergent branches, use `uv run alembic merge heads -m "merge"`.

*Source: fast_api_practice*

---

## 9. Tests use aiosqlite (SQLite) but production uses asyncpg (PostgreSQL)

**Symptom**: Tests pass but production fails on PostgreSQL-specific features
(`ON CONFLICT`, array types, `JSONB`, enum types).

**Root cause**: SQLite doesn't support many PostgreSQL-specific SQL features.

**Fix**: Keep aiosqlite for fast unit tests. Use `docker-compose.test.yml` with a
real PostgreSQL instance for integration tests that exercise PG-specific features.

*Source: fast_api_practice*

---

## 10. Railway `$PORT` environment variable

**Symptom**: Railway health check fails and deploy rolls back even though the app
starts fine locally.

**Root cause**: Railway injects a `PORT` env var that may differ from default 8000.
If the app doesn't bind to `$PORT`, the health check fails.

**Fix**: Use `${PORT:-8000}` in Dockerfile CMD. Add `PORT: int = 8000` to the
`Settings` class as a fallback.

*Source: fast_api_practice*

---

## 11. `docker-entrypoint.sh` must be LF line endings (not CRLF)

**Symptom**: `/bin/bash^M: bad interpreter`

**Root cause**: Windows-style CRLF line endings in shell scripts.

**Fix**: Add to `.gitattributes`:
```
*.sh text eol=lf
```

*Source: fast_api_practice*

---

## 12. Docker BuildKit cache corruption after failed builds

**Symptom**: `parent snapshot … does not exist: not found`

**Fix**: `docker builder prune -f` then `docker build --no-cache …`

*Source: fast_api_practice*

---

## 13. `--chown=appuser:appuser` required on COPY from builder to runtime

**Symptom**: `Permission denied` when running Python in the runtime stage.

**Root cause**: Without `--chown`, copied files are owned by root. The non-root
`appuser` can't execute binaries.

**Fix**: All `COPY --from=builder` instructions must use `--chown=appuser:appuser`.

*Source: fast_api_practice*

---

## 1. passlib bcrypt incompatibility (bcrypt >= 4.1)

**Symptom**: `ValueError: password cannot be longer than 72 bytes, truncate manually if necessary`
when calling `passlib.CryptContext.hash()`.

**Root cause**: passlib's bcrypt wrapper (`passlib.handlers.bcrypt`) is incompatible with bcrypt >= 4.1.
The `_finalize_backend_mixin` method calls `detect_wrap_bug()` which triggers the newer bcrypt
validation before passlib can handle it.

**Fix**: Use `bcrypt` directly instead of `passlib[bcrypt]`:
```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

## 2. DomainError subclass exception handler must walk MRO

**Symptom**: Custom exception subclasses (e.g. `InvalidCredentials(AuthenticationError)`)
return HTTP 400 instead of their parent's mapped status code (401).

**Root cause**: Using `_STATUS_MAP.get(type(exc), 400)` does exact type matching.
`type(InvalidCredentials())` is `InvalidCredentials`, not `AuthenticationError`.

**Fix**: Walk the MRO to find the first matching parent class:
```python
def _resolve_status(exc: DomainError) -> int:
    for cls in type(exc).__mro__:
        if cls in _STATUS_MAP:
            return _STATUS_MAP[cls]
    return 400
```

## 3. SQLite test tables must import models before create_all

**Symptom**: `OperationalError: no such table: users` in tests even though
`Base.metadata.create_all` is called in the setup fixture.

**Root cause**: SQLAlchemy only knows about ORM models that have been imported
and have their `__tablename__` registered with `Base.metadata`. If the test
conftest doesn't import the models, `create_all` creates zero tables.

**Fix**: Add `import src.models` in `tests/conftest.py` before the fixture
that calls `create_all`.

## 4. Hatch build requires explicit package declaration

**Symptom**: `ValueError: Unable to determine which files to ship inside the wheel`
when running `uv sync`.

**Root cause**: Hatchling can't auto-detect the package when the directory name
(`src/`) doesn't match the project name (`learning-platform`).

**Fix**: Add to `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src"]
```
