# Day 2 Implementation Report — Docker Compose + Railway Basics

> **Date:** 2026-04-14
> **Executor:** GitHub Copilot (AI Agent)
> **Branch:** `fastapi-training`
> **Based on:** Day 1 commit `7a24de5`

---

## Summary

Day 2 of the DevOps Training Plan is **complete**. The full stack (app +
PostgreSQL 16 + Redis 7) runs cleanly under Docker Compose, all three services
reach `healthy` status, and `/health` returns `{"status": "healthy", "database":
"connected"}`. Three gotchas were discovered and resolved. Railway config and
`Settings.PORT` are in place for the manual deploy step.

---

## Steps Completed

| Step | Description | Status |
|------|-------------|--------|
| 2.1 | Create `docker-compose.yml` | ✅ Done |
| 2.2 | Create `docker-compose.test.yml` | ✅ Done |
| 2.3 | Verify Docker Compose stack locally | ✅ Done |
| 2.4 | Railway account/CLI setup | 🧑 MANUAL — skipped by agent |
| 2.5 | Create `railway.toml` | ✅ Done |
| 2.6 | Add `Settings.PORT` to `src/core/config.py` | ✅ Done |
| 2.7 | Set Railway environment variables | 🧑 MANUAL — skipped by agent |
| 2.8 | Deploy to Railway | 🧑 MANUAL — skipped by agent |
| 2.9 | Day 2 verification gate + commit | ✅ PASSED (commit pending) |

---

## Files Created / Modified

| File | Action | Notes |
|------|--------|-------|
| `docker-compose.yml` | **Created** | app + PostgreSQL 16 + Redis 7; health checks; named volumes |
| `docker-compose.test.yml` | **Created** | Test runner override; entrypoint cleared; `pytest` as CMD |
| `railway.toml` | **Created** | Dockerfile builder; `startCommand = ./docker-entrypoint.sh`; `/health` check |
| `src/core/config.py` | **Modified** | Added `PORT: int = 8000` (Railway compatibility) |
| `docker-entrypoint.sh` | **Modified** | Changed `exec "$@"` → `exec python -m uvicorn …` (shebang fix) |
| `Dockerfile` | **Modified** | Removed `CMD` (entrypoint now fully handles startup) |
| `alembic/versions/a2235df5580e_…` | **Fixed** | Added `COMMIT` before `ALTER TYPE ADD VALUE` DML |
| `alembic/versions/a1b2c3d4e5f6_…` | **Deleted** | Duplicate fake-ID migration removed |

---

## Verification Gate Results

### Docker Compose `up --build`

```
✔ Image fast_api_practice-app    Built    3.4s
✔ Container fast_api_practice-db-1    Healthy
✔ Container fast_api_practice-redis-1 Healthy
✔ Container fast_api_practice-app-1   Healthy
```

### Health Endpoint

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

```json
{
    "status": "healthy",
    "version": "0.1.0",
    "database": "connected"
}
```

### `docker compose ps` (steady state)

```
NAME                        STATUS
fast_api_practice-app-1     Up (healthy)   0.0.0.0:8000->8000/tcp
fast_api_practice-db-1      Up (healthy)   0.0.0.0:5432->5432/tcp
fast_api_practice-redis-1   Up (healthy)   0.0.0.0:6379->6379/tcp
```

### Lint

```
uv run ruff check src/ tests/         → All checks passed!
uv run ruff format --check src/ tests/ → 64 files already formatted
```

### Tests (host)

```
3 failed, 117 passed in 79.77s
```

- **117 passed** — unchanged from Day 1
- **3 failed** — pre-existing `TestUserListing` (stale tests for removed `GET /users`). Not caused by Day 2 changes.

### `docker compose down`

Stack torn down cleanly; named volumes (`pgdata`, `redisdata`) preserved.

---

## Gotchas Discovered & Resolved

### Gotcha 5 — `uvicorn` venv script has broken shebang (same root cause as `alembic`)

**Problem:** Even with `UV_PYTHON_PREFERENCE=only-system` set during `uv sync`,
the venv wrapper scripts for **all** console-scripts entries (not just `alembic`)
are generated with shebangs that point to the builder-stage Python path
(`/build/.venv/…`). This path doesn't exist in the runtime stage.

The Day 1 entrypoint used `exec "$@"` to pass through the Dockerfile `CMD`. The
`CMD` was:
```dockerfile
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```
When `exec "$@"` runs `sh -c "uvicorn …"`, the inner `sh` (dash) spawns a new
process that looks up `uvicorn` via `PATH` — finds `/app/.venv/bin/uvicorn` — then
fails to execute it because the shebang path is invalid.

**Symptom:**
```
./docker-entrypoint.sh: line N: /app/.venv/bin/uvicorn: cannot execute: required file not found
```

**Fix applied (two changes):**

1. `docker-entrypoint.sh` — replace `exec "$@"` with a direct `python -m uvicorn` call:
   ```bash
   exec python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
   ```
   Using `bash`'s own variable expansion (`${PORT:-8000}`) means no subshell is spawned.

2. `Dockerfile` — remove the `CMD` entirely (the entrypoint now handles all startup).

**General rule:** In multi-stage Docker builds with `uv`, **always use
`python -m <module>`** instead of bare venv script names for any console-script
entry point (`uvicorn`, `alembic`, `gunicorn`, `celery`, etc.).

**Date:** 2026-04-14

---

### Gotcha 6 — `ALTER TYPE ADD VALUE` cannot be used in the same transaction as DML

**Problem:** Alembic wraps all steps in a single transaction by default. PostgreSQL
requires `ALTER TYPE … ADD VALUE` to be fully committed before any `UPDATE` or
`INSERT` can reference the new enum value in the same session.

**Symptom:**
```
asyncpg.exceptions.UnsafeNewEnumValueUsageError: unsafe use of new value "user"
  of enum type user_role_enum
HINT: New enum values must be committed before they can be used.
```

This affected both enum changes in migration `a2235df5580e`:
- `user_role_enum ADD VALUE 'user'` → blocked the `UPDATE users SET role = 'user'`
- `project_member_role_enum ADD VALUE 'admin'` → blocked the `UPDATE project_members SET role = 'admin'`

**Fix applied:** Use `op.get_bind()` to issue raw SQL and manually commit/begin
transactions around each `ADD VALUE`:
```python
bind = op.get_bind()
bind.execute(sa_text("COMMIT"))
bind.execute(sa_text("ALTER TYPE user_role_enum ADD VALUE IF NOT EXISTS 'user'"))
bind.execute(sa_text("COMMIT"))
bind.execute(sa_text("ALTER TYPE project_member_role_enum ADD VALUE IF NOT EXISTS 'admin'"))
bind.execute(sa_text("COMMIT"))
bind.execute(sa_text("BEGIN"))
# ... DML referencing new values now safe ...
```

**Date:** 2026-04-14

---

### Gotcha 7 — Multiple Alembic heads crash container startup

**Problem:** Two migration files (`a1b2c3d4e5f6` and `a2235df5580e`) both had
`down_revision = "120e14d02e4d"`, creating a branch. `alembic upgrade head`
(singular) fails at startup:

```
FAILED: Multiple head revisions are present for given argument 'head';
please specify a specific target revision…
```

**Root cause:** `a1b2c3d4e5f6` was a hand-written file with a fake round-number
ID and a hardcoded timestamp (`2026-03-27 10:00:00`). It was a duplicate of the
autogenerated `a2235df5580e` (timestamp `2026-03-27 18:13:26`).

**Fix applied:** Deleted `a1b2c3d4e5f6_simplify_roles_to_project_level.py`.
Confirmed single head with `uv run alembic heads`.

**Prevention:** Always check for multiple heads before adding a new migration:
```bash
uv run alembic heads    # should show exactly one (head) line
```
If multiple heads exist, use `uv run alembic merge heads -m "merge"` rather than
deleting files (unless one is clearly a duplicate).

**Date:** 2026-04-14

---

## Final File States

### `docker-compose.yml` (key decisions)

| Decision | Reason |
|----------|--------|
| `depends_on: db: condition: service_healthy` | App waits for PG to be ready before running migrations |
| `postgres:16-alpine`, `redis:7-alpine` | Small, stable, Alpine-based images |
| Named volumes `pgdata`, `redisdata` | Data persists across `docker compose down` (volumes not removed unless `-v`) |
| Dedicated `backend` network | Services communicate by name; no external exposure between them |
| `restart: unless-stopped` | Auto-restarts on crash, stops only on explicit `docker compose down` |

### `docker-entrypoint.sh` (final)

```bash
#!/bin/bash
set -euo pipefail

echo "==> Running database migrations..."
python -m alembic upgrade head

echo "==> Starting application..."
# python -m uvicorn avoids broken venv script shebangs in multi-stage builds
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

### `railway.toml` (key decisions)

| Field | Value | Reason |
|-------|-------|--------|
| `builder` | `"DOCKERFILE"` | Opt out of Nixpacks auto-detection |
| `startCommand` | `"./docker-entrypoint.sh"` | Runs migrations then uvicorn; `$PORT` handled inside script |
| `healthcheckPath` | `"/health"` | Railway probes this after deploy; rolls back if it fails |
| `restartPolicyType` | `"ON_FAILURE"` | Auto-restarts on crash, not on intentional stop |

---

## Manual Steps Remaining (🧑 Human Required)

| Step | Command |
|------|---------|
| Install Railway CLI | `npm install -g @railway/cli` or `brew install railway` |
| Login | `railway login` |
| Create project | `railway init` |
| Link repo | `railway link` |
| Set env vars | `railway variables set DATABASE_URL="…" JWT_SECRET_KEY="…" DEBUG="false"` |
| Deploy | `git push origin main` (auto-deploy if connected) or `railway up --detach` |
| Verify | `curl -s https://<app>.up.railway.app/health` |

---

## Ready for Day 3

Day 3 prerequisites are met:

- ✅ `docker compose up -d --build` — all 3 services healthy
- ✅ `/health` → `{"status": "healthy", "database": "connected"}`
- ✅ `docker compose down` — clean teardown
- ✅ `railway.toml` in place with health check path
- ✅ `Settings.PORT` added for Railway `$PORT` compatibility
- ✅ `docker-entrypoint.sh` uses `python -m uvicorn` (shebang-safe)
- ✅ Alembic single head confirmed
- ✅ 117 tests pass on host; lint clean
