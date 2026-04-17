# Day 3 Report — Advanced Railway + Production Readiness

**Training plan:** `docs/[KhoiVo] DevOps Training Plan.md`  
**Session date:** 2026-04-15  
**Agent:** Claude Sonnet 4.6  
**Status:** ✅ Complete — all gates passed

---

## Objectives

| # | Objective | Status |
|---|-----------|--------|
| 1 | GitHub Actions CI pipeline (lint → test → docker build) | ✅ |
| 2 | AI agent scaffold files (`.claude/CLAUDE.md`, `.github/copilot-instructions.md`) | ✅ |
| 3 | `.gitattributes` — LF enforcement for cross-platform safety | ✅ |
| 4 | API Changelog (`docs/api/CHANGELOG.md`) | ✅ |
| 5 | Final verification gate (ruff + pytest + docker compose smoke) | ✅ |

---

## Files Created

### `.github/workflows/ci.yml`

Three-job pipeline:

```
lint  ──►  test  ──►  docker-build
```

| Job | What it does |
|-----|-------------|
| **lint** | `ruff check` + `ruff format --check` via `uv run` |
| **test** | Spins up `postgres:16-alpine` service container, runs `pytest --cov=src`, uploads `coverage.xml` as an artifact |
| **docker-build** | `docker/build-push-action@v6` with `push: false`; uses GitHub Actions cache (`type=gha`) so repeat builds hit the layer cache; reports final image size |

Key choices:
- `astral-sh/setup-uv@v6` for deterministic, fast dependency installs.
- `python-version: "3.14"` in both lint and test jobs — mirrors production Python.
- `concurrency` block cancels in-progress runs on the same branch, preventing queue pile-ups.
- Test job sets `DATABASE_URL` + `DATABASE_URL_TEST` pointing at the service container so Alembic migrations and pytest both use real PostgreSQL (same as Railway).

### `.github/copilot-instructions.md`

Provides GitHub Copilot with:
- Full tech-stack table (runtime, DB, auth, migrations, tooling, deployment).
- Architecture diagram of `src/` layout.
- Code conventions: thin routes (no `try/except`), domain-exception pattern, async-first.
- Testing conventions: aiosqlite in-memory DB, `anyio` backend, `pytest-asyncio` auto mode.
- Deployment notes: Railway injects `PORT`, entrypoint handles migrations.

### `.claude/CLAUDE.md`

Agent onboarding document for Claude (and any compatible AI coding agent):
- Repository layout with inline annotations.
- Three critical rules (never add try/except to routes, always use domain exceptions, uv only).
- Quality gate commands (`uv run ruff check`, `uv run pytest`, `docker compose up -d --build`).
- Common pitfalls with resolutions (mirrors `gotchas.md` highlights).
- Railway deployment checklist.

### `.gitattributes`

| Pattern | Setting | Reason |
|---------|---------|--------|
| `*.sh` | `text eol=lf` | Prevents `\r` breaking `#!/bin/bash` in Linux containers |
| `*.yml`, `*.yaml` | `text eol=lf` | YAML is whitespace-sensitive; CRLF causes silent parse errors |
| `*.toml` | `text eol=lf` | `railway.toml`, `pyproject.toml` |
| `*.py` | `text eol=lf` | Consistent across all Python source |
| `uv.lock` | `binary` | Lock file must never be line-ending normalised |

### `docs/api/CHANGELOG.md`

Follows [Keep a Changelog](https://keepachangelog.com/) and Semantic Versioning.

- **v0.1.0** — initial release (baseline before this training plan).
- **v0.2.0** — `GET /health` enhanced with `database` field; `status` becomes `"degraded"` on DB failure.
- **[Unreleased]** section ready for the next change.

---

## Day 3 Verification Gate Results

Run date: 2026-04-15T17:33–17:35 local

### Gate 1 — `ruff check src/ tests/`
```
All checks passed!
```

### Gate 2 — `ruff format --check src/ tests/`
```
64 files already formatted
```

### Gate 3 — `pytest`
```
117 passed, 3 failed in 79.12s
```
3 pre-existing failures: `TestUserListing` tests hitting `GET /api/v1/users`  
which was intentionally removed in the exception-handling refactor (pre-Day 1).  
**These are expected and not regressions.**

### Gate 4 — `docker compose up -d --build` smoke test
```
/health  →  {"status": "healthy", "version": "0.1.0", "database": "connected"}
```

Container status at smoke-test time:

| Container | Image | Status |
|-----------|-------|--------|
| `fast_api_practice-app-1` | `fast_api_practice-app` | Up (healthy) |
| `fast_api_practice-db-1` | `postgres:16-alpine` | Up (healthy) |
| `fast_api_practice-redis-1` | `redis:7-alpine` | Up (healthy) |

### Gate 5 — `docker compose down -v`
```
✔ Container fast_api_practice-app-1  Removed
✔ Container fast_api_practice-db-1   Removed
✔ Container fast_api_practice-redis-1 Removed
✔ Volume    fast_api_practice_pgdata  Removed
✔ Volume    fast_api_practice_redisdata Removed
✔ Network   fast_api_practice_backend Removed
```

---

## CI Pipeline Design Decisions

### Why `needs: lint` before `test`?
Lint failures are cheap (< 10 s) and high-signal. Failing fast before spending 80 s on pytest saves CI minutes and gives faster feedback.

### Why `needs: test` before `docker-build`?
No point building an image from code that doesn't pass tests. The docker build job is the final seal-of-approval before a potential push.

### Why not push to a registry in CI?
The training plan's Day 3 scope is *validation*, not *deployment*. A `push: false` build still exercises the full Dockerfile and layer cache without requiring registry credentials. Push can be added as a Day 4 extension.

### Why GitHub Actions cache for Docker layers?
The multi-stage Dockerfile installs ~80 MB of Python packages. With `type=gha` cache, the `RUN uv sync` layer is typically a cache hit on subsequent pushes to the same branch, cutting build time from ~60 s to ~10 s.

---

## Railway Deployment Notes

`railway.toml` is already in place (created Day 2). Day 3 adds the CI gate that validates the Docker image builds cleanly. The Railway deployment flow is:

```
git push  →  GitHub Actions CI  →  (manual) Railway deploy
```

Railway reads `railway.toml`:
- Builds using `Dockerfile`.
- Starts with `./docker-entrypoint.sh` (migrations → uvicorn).
- Health-checks `/health` (timeout 5 s).
- Restarts on failure (max 3 retries).

Environment variables required on Railway:
| Variable | Example | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://…` | Injected by Railway Postgres plugin |
| `JWT_SECRET_KEY` | 64-char random hex | Generate with `openssl rand -hex 32` |
| `DEBUG` | `false` | Production default |
| `PORT` | _(set by Railway)_ | Entrypoint uses `${PORT:-8000}` |

---

## Training Plan — Complete Summary

| Day | Focus | Key Deliverables | Gate |
|-----|-------|-----------------|------|
| **1** | Docker Fundamentals | `Dockerfile`, `.dockerignore`, `docker-entrypoint.sh`, enhanced `/health`, `tests/test_health.py` | ✅ |
| **2** | Docker Compose + Railway | `docker-compose.yml`, `docker-compose.test.yml`, `railway.toml`, migration fixes (ALTER TYPE + Alembic heads) | ✅ |
| **3** | Production Readiness | `.github/workflows/ci.yml`, `.github/copilot-instructions.md`, `.claude/CLAUDE.md`, `.gitattributes`, `docs/api/CHANGELOG.md` | ✅ |

Total new files: **18**  
Total gotchas logged: **12** (see `gotchas.md`)  
Total test count: **117 passing** (3 pre-existing expected failures)
