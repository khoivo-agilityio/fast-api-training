# DevOps Training — Step-by-Step Execution Plan

> **Target executor:** AI Agent — Claude Sonnet 4.6
> **Source document:** `docs/[KhoiVo] DevOps Training Plan.md`
> **Project:** Collaborative Project & Task Management API (FastAPI)
> **Date:** 2025-07-11

---

## Table of Contents

1. [Prompt Review](#1-prompt-review)
2. [Pre-Flight Checklist](#2-pre-flight-checklist)
3. [Questions & Clarifications](#3-questions--clarifications)
4. [Day 1 — Docker Fundamentals](#4-day-1--docker-fundamentals)
5. [Day 2 — Docker Compose + Railway Basics](#5-day-2--docker-compose--railway-basics)
6. [Day 3 — Advanced Railway + Production Readiness](#6-day-3--advanced-railway--production-readiness)
7. [Post-Implementation Checklist](#7-post-implementation-checklist)
8. [API Changelog](#8-api-changelog)
9. [File Manifest](#9-file-manifest)

---

## 1. Prompt Review

### Original Prompt (paraphrased)

> Create a detailed step-by-step execution plan for the DevOps Training Plan document.
> The plan must include: the original prompt with pros/cons analysis, execution and
> verification steps (linting + testing), detailed specs targeting AI Agent Claude
> Sonnet 4.6, gotchas logging to `gotchas.md`, instruction updates to
> `.claude/CLAUDE.md` and `.github/copilot-instructions.md`, all changes needed
> (DTOs, decorators, controllers, services, tests), and an API changelog in `docs/api`.

### Pros

| # | Pro | Why |
|---|-----|-----|
| 1 | **Structured deliverables** | Explicitly lists every artifact (gotchas, CLAUDE.md, copilot-instructions, changelog), reducing ambiguity. |
| 2 | **Verification-first mindset** | Requiring linting and testing steps ensures quality gates are built into the plan, not bolted on. |
| 3 | **AI-agent targeting** | Calling out "Claude Sonnet 4.6" forces the plan to be _deterministically executable_ — no hand-wavy prose. |
| 4 | **Scaffolding awareness** | Mandating `.claude/CLAUDE.md` and `.github/copilot-instructions.md` promotes consistent AI-assisted development across sessions. |
| 5 | **Living documentation** | `gotchas.md` and the API changelog create institutional memory that outlives any single session. |

### Cons / Mismatches

| # | Con | Mitigation |
|---|-----|------------|
| 1 | **Template mismatch — "DTOs, decorators, controllers, services, tests"** | This is a generic API-feature template. A DevOps/infra task produces _Dockerfiles, Compose files, CI/CD workflows, railway configs, and health-check enhancements_ — not new DTOs or decorators. This plan maps those generic slots to their infra equivalents (see §3). |
| 2 | **No explicit rollback strategy** | Docker/Railway changes are additive and version-controlled, so `git revert` suffices — but the plan should note this. |
| 3 | **"API changelog" for non-API work** | The only API-surface change is an enhanced `/health` endpoint. The changelog entry will be minimal. This plan creates `docs/api/CHANGELOG.md` for consistency but notes the scope. |
| 4 | **Railway requires manual account/project setup** | An AI agent cannot click through a web dashboard. The plan marks those steps as `🧑 MANUAL` and provides the exact CLI equivalents where possible. |
| 5 | **Missing cost/billing acknowledgement** | Railway has usage-based billing. The plan includes a cost-control note in Day 3. |

### Template Slot Mapping (API Feature → DevOps/Infra)

| Generic Slot | DevOps Equivalent |
|---|---|
| DTOs / Schemas | Environment variable schemas (`Settings` class updates) |
| Decorators | N/A — no new decorators |
| Controllers / Routes | Health-check endpoint enhancements |
| Services | N/A — no new domain services |
| Tests | Dockerfile build tests, Compose smoke tests, health endpoint tests |
| API Changelog | `docs/api/CHANGELOG.md` — documents `/health` changes |

---

## 2. Pre-Flight Checklist

Before executing any step, the agent **MUST** verify:

```
[ ] Python 3.14+ available (matches pyproject.toml requires-python)
[ ] Docker Desktop / Docker Engine installed and daemon running
[ ] docker compose v2 plugin available (docker compose version)
[ ] Git repo is clean (no uncommitted changes)
[ ] All 108 tests pass: uv run pytest --tb=short
[ ] Ruff lint passes:   uv run ruff check src/ tests/
[ ] .env file exists with valid DATABASE_URL and JWT_SECRET_KEY
[ ] PostgreSQL is accessible at the DATABASE_URL
```

**Verification command block (run all at once):**

```bash
python --version
docker --version
docker compose version
git status --porcelain
uv run pytest --tb=short -q
uv run ruff check src/ tests/
```

> ⚠️ If any check fails, STOP and resolve before proceeding.

---

## 3. Questions & Clarifications

The following questions were identified and resolved inline. If the executor
(AI agent or human) encounters ambiguity, apply the **Default Resolution**.

| # | Question | Default Resolution |
|---|----------|-------------------|
| Q1 | The training plan mentions "Node.js or Python app" — which do we containerize? | **Python (FastAPI)** — this is the project under development. |
| Q2 | Should we push images to Docker Hub? | **No** — Railway builds from GitHub repo directly. We tag locally for testing only. |
| Q3 | The plan mentions "Frontend (React/Next.js)" in the Capstone — do we build a frontend? | **No** — this is a backend-only project. The capstone deploys the existing FastAPI app + PostgreSQL + Redis. |
| Q4 | Which Python base image? | `python:3.12-slim` — 3.14 slim images may not be stable on all platforms; 3.12-slim is the pragmatic choice for production. Update when 3.14-slim is GA. |
| Q5 | Redis — does the app currently use Redis? | **No** — but Docker Compose will provision it for future use (caching, rate-limiting, WebSocket pub/sub). The app won't crash without it. |
| Q6 | Railway plan tier? | **Free trial / Hobby** — sufficient for training. The plan notes upgrade paths. |
| Q7 | DTOs, decorators, controllers, services, tests — do these apply? | **Partially.** See Template Slot Mapping in §1. Only the `/health` endpoint and `Settings` class are touched. |
| Q8 | Should tests run _inside_ Docker or only on the host? | **Both.** Host-based `uv run pytest` for fast iteration; `docker compose run --rm app pytest` for environment parity. |
| Q9 | CI/CD target — GitHub Actions or Railway auto-deploy? | **Both.** GitHub Actions for lint + test gate; Railway auto-deploy on push to `main`. |
| Q10 | Database migration strategy in Docker? | Alembic migrations run at container startup via an entrypoint script, _before_ uvicorn starts. |

---

## 4. Day 1 — Docker Fundamentals

### Goal

Containerize the FastAPI application with a production-grade, multi-stage Dockerfile.
All existing tests must still pass. Image size target: **< 250 MB**.

---

### Step 1.1 — Create `.dockerignore`

**What:** Prevent unnecessary files from entering the Docker build context.

**File:** `.dockerignore` (project root)

```dockerignore
# Version control
.git
.gitignore

# Python artifacts
__pycache__
*.py[cod]
*.egg-info
.eggs
dist
build

# Virtual environments
.venv
venv
.tox

# IDE / editor
.vscode
.idea
*.swp
*.swo

# Environment files (secrets — never bake into image)
.env
.env.*
!.env.example

# Test / coverage artifacts
.pytest_cache
.ruff_cache
.coverage
htmlcov
reports

# Documentation (not needed at runtime)
docs

# OS files
.DS_Store
Thumbs.db

# Docker (avoid recursive context)
docker-compose*.yml
Dockerfile*
```

**Verification:**

```bash
# Build context should be small — check with:
docker build --no-cache -t test-context-size . 2>&1 | head -5
# Look for "Sending build context to Docker daemon  XX.XXkB"
# Should be < 5 MB (before adding Dockerfile)
```

---

### Step 1.2 — Create production Dockerfile (multi-stage)

**What:** Two-stage build — `builder` installs dependencies, `runtime` copies only what's needed.

**File:** `Dockerfile` (project root)

```dockerfile
# ============================================================
# Stage 1: Builder — install Python dependencies
# ============================================================
FROM python:3.12-slim AS builder

# Prevents Python from writing .pyc files and enables unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install system deps needed to compile async drivers (asyncpg, bcrypt)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency manifests first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies into a virtual environment
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# ============================================================
# Stage 2: Runtime — minimal image
# ============================================================
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Tell Python where the venv lives
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Runtime system deps only (no compiler)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

# Copy virtual environment and source from builder
COPY --from=builder /build/.venv ./.venv
COPY --from=builder /build/src ./src
COPY --from=builder /build/alembic ./alembic
COPY --from=builder /build/alembic.ini ./

# Copy entrypoint
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key decisions:**

- `python:3.12-slim` — ~120 MB base, well-tested.
- `uv sync --frozen --no-dev` — reproducible, no dev deps in prod.
- Non-root `appuser` — security best practice.
- `HEALTHCHECK` — enables Docker/Compose health monitoring.
- `curl` installed in runtime for healthcheck; alternatively use a Python-based check.

---

### Step 1.3 — Create `docker-entrypoint.sh`

**What:** Runs Alembic migrations before starting the app server.

**File:** `docker-entrypoint.sh` (project root)

```bash
#!/bin/bash
set -euo pipefail

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Starting application..."
exec "$@"
```

**Verification:**

```bash
chmod +x docker-entrypoint.sh
shellcheck docker-entrypoint.sh  # if shellcheck is installed
```

---

### Step 1.4 — Build and test the Docker image locally

**Execution:**

```bash
# Build the image
docker build -t task-manager-api:dev .

# Verify image size (target: < 250 MB)
docker images task-manager-api:dev --format "{{.Size}}"

# Inspect layers
docker history task-manager-api:dev

# Quick smoke test (will fail without DB, but verifies the image boots)
docker run --rm -e DATABASE_URL="postgresql+asyncpg://x:x@host:5432/x" \te
    -e JWT_SECRET_KEY="test-secret-key-at-least-32-chars-long" \
    task-manager-api:dev python -c "from src.main import app; print('✅ App imported successfully')"
```

**Verification checklist:**

```
[ ] docker build completes without errors
[ ] Image size < 250 MB
[ ] Non-root user: docker run --rm task-manager-api:dev whoami  →  "appuser"
[ ] Python import smoke test passes
```

---

### Step 1.5 — Enhance the `/health` endpoint

**What:** Add database connectivity check and version info for production monitoring.

**File:** `src/schemas/common.py` — update `HealthResponse`

```python
# Add to HealthResponse:
class HealthResponse(BaseModel):
    status: str          # "healthy" | "degraded" | "unhealthy"
    version: str
    database: str = "unknown"  # "connected" | "disconnected" | "unknown"
```

**File:** `src/main.py` — update health check route

```python
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    from src.infrastructure.database.connection import async_engine
    db_status = "unknown"
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    overall = "healthy" if db_status == "connected" else "degraded"
    return HealthResponse(status=overall, version="0.1.0", database=db_status)
```

**Verification:**

```bash
# Lint
uv run ruff check src/schemas/common.py src/main.py

# Existing tests must pass
uv run pytest tests/ --tb=short -q

# Add a test for the enhanced health endpoint
# (see Step 1.6)
```

---

### Step 1.6 — Add health endpoint tests

**File:** `tests/test_health.py` (new file)

```python
"""Tests for the /health endpoint."""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for GET /health."""

    async def test_health_returns_200(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "database" in data

    async def test_health_response_schema(self, client):
        response = await client.get("/health")
        data = response.json()
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
        assert data["database"] in ("connected", "disconnected", "unknown")
```

**Verification:**

```bash
uv run pytest tests/test_health.py -v
uv run ruff check tests/test_health.py
```

---

### Step 1.7 — Day 1 verification gate

**All of these must pass before moving to Day 2:**

```bash
# Full test suite
uv run pytest --tb=short -q

# Lint
uv run ruff check src/ tests/

# Docker build
docker build -t task-manager-api:dev .

# Image size check
SIZE=$(docker images task-manager-api:dev --format "{{.Size}}")
echo "Image size: $SIZE"

# Git commit
git add -A
git commit -m "feat(docker): add Dockerfile, .dockerignore, entrypoint, enhanced health check

- Multi-stage Dockerfile with python:3.12-slim
- Non-root user (appuser) for security
- docker-entrypoint.sh runs Alembic migrations before server start
- Enhanced /health endpoint with database connectivity check
- Added health endpoint tests
- Image size target: < 250 MB"
```

---

## 5. Day 2 — Docker Compose + Railway Basics

### Goal

Orchestrate the full stack locally (app + PostgreSQL + Redis) with Docker Compose,
then deploy to Railway.

---

### Step 2.1 — Create `docker-compose.yml`

**File:** `docker-compose.yml` (project root)

```yaml
# docker-compose.yml — Local development stack
services:
  # ── Application ──────────────────────────────────────────
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://taskmanager:taskmanager_dev@db:5432/fast_api_practice_dev
      - JWT_SECRET_KEY=local-dev-secret-key-at-least-32-characters
      - DEBUG=true
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - backend

  # ── PostgreSQL ───────────────────────────────────────────
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: taskmanager
      POSTGRES_PASSWORD: taskmanager_dev
      POSTGRES_DB: fast_api_practice_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskmanager -d fast_api_practice_dev"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped
    networks:
      - backend

  # ── Redis (for future caching / WebSocket pub-sub) ──────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    restart: unless-stopped
    networks:
      - backend

volumes:
  pgdata:
  redisdata:

networks:
  backend:
    driver: bridge
```

**Key decisions:**

- `depends_on` with `condition: service_healthy` — app waits for DB to be ready.
- Named volumes `pgdata` and `redisdata` — data persists across restarts.
- `postgres:16-alpine` and `redis:7-alpine` — small, stable images.
- Dedicated `backend` network — services communicate by service name.

---

### Step 2.2 — Create `docker-compose.test.yml` (test override)

**What:** Run the full test suite inside Docker for environment parity.

**File:** `docker-compose.test.yml` (project root)

```yaml
# docker-compose.test.yml — Run tests inside Docker
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://taskmanager:taskmanager_dev@db:5432/fast_api_practice_test
      - DATABASE_URL_TEST=postgresql+asyncpg://taskmanager:taskmanager_dev@db:5432/fast_api_practice_test
      - JWT_SECRET_KEY=test-secret-key-at-least-32-characters-long
      - DEBUG=true
    depends_on:
      db:
        condition: service_healthy
    # Override entrypoint to run tests instead of the app server
    entrypoint: []
    command: ["python", "-m", "pytest", "--tb=short", "-q"]
    networks:
      - backend

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: taskmanager
      POSTGRES_PASSWORD: taskmanager_dev
      POSTGRES_DB: fast_api_practice_test
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskmanager -d fast_api_practice_test"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

---

### Step 2.3 — Verify Docker Compose locally

**Execution:**

```bash
# Start the full stack
docker compose up -d --build

# Wait for health checks
docker compose ps

# Verify app is healthy
curl -s http://localhost:8000/health | python -m json.tool

# Expected output:
# {
#     "status": "healthy",
#     "version": "0.1.0",
#     "database": "connected"
# }

# Check logs
docker compose logs app --tail=20

# Run tests inside Docker
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
echo "Exit code: $?"

# Tear down
docker compose down
```

**Verification checklist:**

```
[ ] docker compose up --build succeeds
[ ] curl localhost:8000/health returns {"status": "healthy", ...}
[ ] docker compose -f docker-compose.test.yml passes all tests
[ ] docker compose down cleans up (no orphan containers)
[ ] Named volumes persist data across up/down cycles
```

---

### Step 2.4 — Railway setup

> 🧑 **MANUAL STEPS** — These require browser / account access.

| # | Action | CLI Alternative |
|---|--------|----------------|
| 1 | Create Railway account at [railway.com](https://railway.com) | N/A |
| 2 | Install Railway CLI | `npm install -g @railway/cli` or `brew install railway` |
| 3 | Login via CLI | `railway login` |
| 4 | Create a new project | `railway init` |
| 5 | Link GitHub repo | `railway link` (select the repo) |

**Post-setup verification:**

```bash
railway --version
railway status
```

---

### Step 2.5 — Create `railway.toml`

**File:** `railway.toml` (project root)

```toml
[build]
# Use the Dockerfile (not Nixpacks)
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
# Start command (overrides Dockerfile CMD if needed)
startCommand = "./docker-entrypoint.sh uvicorn src.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 5
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Key decisions:**

- Explicit `builder = "DOCKERFILE"` — don't rely on Nixpacks auto-detection.
- `$PORT` — Railway injects this env var; the app must bind to it.
- `healthcheckPath` — Railway pings this to verify deployment succeeded.

---

### Step 2.6 — Update `Settings` for Railway compatibility

**What:** Ensure the app binds to Railway's `$PORT` and handles Railway's `DATABASE_URL` format.

**File:** `src/core/config.py` — add `PORT` field

```python
class Settings(BaseSettings):
    # ...existing fields...

    # Server — Railway injects PORT
    PORT: int = 8000
```

**File:** `Dockerfile` — update CMD to use `$PORT`

```dockerfile
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

> **Note:** The `railway.toml` `startCommand` takes precedence on Railway; the Dockerfile CMD is the local fallback.

---

### Step 2.7 — Railway environment variables

> 🧑 **MANUAL** — Set via Railway dashboard or CLI.

```bash
# Required variables (set in Railway dashboard → Variables)
railway variables set DATABASE_URL="<railway-provided-postgres-url>"
railway variables set JWT_SECRET_KEY="<generate-with-secrets.token_urlsafe(64)>"
railway variables set DEBUG="false"
railway variables set PORT="8000"  # Railway auto-sets this, but be explicit
```

---

### Step 2.8 — Deploy to Railway

```bash
# Option A: Push to GitHub (auto-deploys if connected)
git push origin main

# Option B: Deploy via CLI
railway up --detach
```

**Verification:**

```bash
# Check deployment status
railway status

# Check logs
railway logs --tail 50

# Hit the health endpoint
curl -s https://<your-app>.up.railway.app/health | python -m json.tool
```

---

### Step 2.9 — Day 2 verification gate

```bash
# Local Docker Compose
docker compose up -d --build
curl -sf http://localhost:8000/health | python -m json.tool
docker compose down

# Full test suite (host)
uv run pytest --tb=short -q

# Lint
uv run ruff check src/ tests/

# Git commit
git add -A
git commit -m "feat(compose): add Docker Compose stack + Railway config

- docker-compose.yml: app + PostgreSQL 16 + Redis 7
- docker-compose.test.yml: test runner with Dockerized DB
- railway.toml: Dockerfile builder, health check, restart policy
- Settings.PORT for Railway compatibility
- All 108+ tests pass locally and in Docker"
```

---

## 6. Day 3 — Advanced Railway + Production Readiness

### Goal

Optimize the Docker image, set up CI/CD with GitHub Actions, and add monitoring.

---

### Step 3.1 — Optimize Dockerfile

**What:** Apply build-cache optimization and security hardening.

**Changes to `Dockerfile`:**

1. Pin exact package versions in `apt-get install`.
2. Add `--mount=type=cache` for pip/uv cache (BuildKit).
3. Remove `apt` lists in the same `RUN` layer.
4. Ensure `.dockerignore` excludes `tests/` for production image.

**Add to `.dockerignore`:**

```dockerignore
# Exclude tests from production image
tests/
```

**Verification:**

```bash
# Rebuild and check size
docker build -t task-manager-api:optimized .
docker images task-manager-api:optimized --format "{{.Size}}"
# Target: < 200 MB

# Ensure no secrets in image
docker run --rm task-manager-api:optimized env | grep -i secret
# Should return nothing
```

---

### Step 3.2 — Create GitHub Actions CI/CD workflow

**File:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.12"

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --frozen --dev

      - name: Ruff lint
        run: uv run ruff check src/ tests/

      - name: Ruff format check
        run: uv run ruff format --check src/ tests/

  test:
    name: Test
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: taskmanager
          POSTGRES_PASSWORD: taskmanager_dev
          POSTGRES_DB: fast_api_practice_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U taskmanager -d fast_api_practice_test"
          --health-interval 5s
          --health-timeout 3s
          --health-retries 5

    env:
      DATABASE_URL: postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_test
      DATABASE_URL_TEST: postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_test
      JWT_SECRET_KEY: ci-test-secret-key-at-least-32-characters-long
      DEBUG: "true"

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --frozen --dev

      - name: Run tests with coverage
        run: uv run pytest --tb=short --cov=src --cov-report=xml --cov-report=term-missing

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml

  docker-build:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: false
          tags: task-manager-api:ci-${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Verify image size
        run: |
          docker images task-manager-api:ci-${{ github.sha }} --format "{{.Size}}"
```

---

### Step 3.3 — Create `.github/copilot-instructions.md`

**File:** `.github/copilot-instructions.md`

```markdown
# Copilot Instructions — Collaborative Task Manager API

## Project Overview

FastAPI-based Trello/Jira-like backend with JWT auth, RBAC, async PostgreSQL,
WebSocket notifications, and Docker/Railway deployment.

## Tech Stack

- **Runtime:** Python 3.12+ (targeting 3.14), FastAPI, Uvicorn
- **Database:** PostgreSQL 16 via SQLAlchemy 2.0 async + asyncpg
- **Auth:** PyJWT + bcrypt (access + refresh tokens)
- **Migrations:** Alembic
- **Package manager:** uv (with pyproject.toml + uv.lock)
- **Linting:** Ruff
- **Testing:** pytest + pytest-asyncio + httpx + aiosqlite (in-memory)
- **Containerization:** Docker (multi-stage), Docker Compose
- **Deployment:** Railway (Dockerfile builder)
- **CI/CD:** GitHub Actions

## Architecture

```
src/
├── api/v1/          # Route handlers (thin — no business logic)
├── core/            # Config (pydantic-settings), security utils
├── domain/
│   ├── exceptions.py  # Custom domain exceptions (DomainError hierarchy)
│   ├── models/        # SQLAlchemy ORM models
│   └── services/      # Business logic layer
├── infrastructure/    # DB connection, logging, email
├── schemas/           # Pydantic DTOs (request/response)
├── websockets/        # WebSocket notification router
└── main.py            # App factory, exception handlers, middleware
```

## Key Conventions

1. **Exception handling:** Services raise domain exceptions (`NotFoundError`,
   `AuthorizationError`, etc.). Global handlers in `main.py` convert them to
   JSON responses. Route handlers have NO try/except blocks.
2. **Dependency injection:** Use FastAPI `Depends()` for DB sessions, auth, services.
3. **Async everywhere:** All DB operations use `async/await`.
4. **Tests:** Use `aiosqlite` in-memory DB (not real PostgreSQL).
5. **Commits:** Use conventional commits (`feat:`, `fix:`, `docs:`, `ci:`).
6. **Docker:** Multi-stage build. Non-root user. `docker-entrypoint.sh` runs migrations.
7. **Environment:** All config via env vars (12-factor). See `.env.example`.

## Common Commands

```bash
uv run pytest --tb=short -q              # Run tests
uv run ruff check src/ tests/            # Lint
uv run ruff format src/ tests/           # Format
docker compose up -d --build             # Start local stack
docker compose down                      # Stop local stack
docker compose logs app --tail=50        # View logs
alembic upgrade head                     # Run migrations
alembic revision --autogenerate -m "..."  # Create migration
```

## Gotchas

See `gotchas.md` in the project root for known issues and workarounds.
```

---

### Step 3.4 — Create `.claude/CLAUDE.md`

**File:** `.claude/CLAUDE.md`

```markdown
# CLAUDE.md — Agent Instructions

## About This Project

Collaborative Project & Task Management API — a Trello/Jira-like backend built
with FastAPI. See `README.md` for full documentation.

## Repository Layout

```
fast_api_practice/
├── src/                  # Application source
│   ├── api/v1/           # Route handlers (NO try/except — use domain exceptions)
│   ├── core/config.py    # Settings (pydantic-settings, env-driven)
│   ├── domain/
│   │   ├── exceptions.py # DomainError → NotFoundError, AuthorizationError, etc.
│   │   ├── models/       # SQLAlchemy async ORM models
│   │   └── services/     # Business logic (raise domain exceptions)
│   ├── infrastructure/   # DB connection, logging, email
│   ├── schemas/          # Pydantic request/response DTOs
│   ├── websockets/       # Real-time notifications
│   └── main.py           # App factory, global exception handlers
├── tests/                # pytest + pytest-asyncio (aiosqlite in-memory)
├── alembic/              # Database migrations
├── Dockerfile            # Multi-stage production build
├── docker-compose.yml    # Local dev: app + PostgreSQL 16 + Redis 7
├── docker-compose.test.yml  # Test runner in Docker
├── railway.toml          # Railway deployment config
├── .github/workflows/    # CI/CD (lint → test → docker build)
├── pyproject.toml        # Dependencies, ruff, pytest config
├── uv.lock               # Locked dependencies
└── docs/                 # Documentation, plans, changelogs
```

## Critical Rules

1. **NEVER add try/except in route handlers.** Services raise domain exceptions;
   global handlers in `main.py` catch them.
2. **ALWAYS run tests after changes:** `uv run pytest --tb=short -q`
3. **ALWAYS run linter after changes:** `uv run ruff check src/ tests/`
4. **Use conventional commits:** `feat:`, `fix:`, `docs:`, `ci:`, `refactor:`
5. **Environment variables:** All config via `.env`. NEVER hardcode secrets.
6. **Database:** Async PostgreSQL (asyncpg). Tests use aiosqlite in-memory.
7. **Python version:** `requires-python = ">=3.14"` in pyproject.toml. Docker uses 3.12-slim
   (until 3.14-slim is production-ready).

## Before Committing

```bash
uv run ruff check src/ tests/       # Must pass
uv run ruff format --check src/ tests/  # Must pass
uv run pytest --tb=short -q         # Must pass (108+ tests)
```

## Known Gotchas

See `gotchas.md` in the project root.

## Key Files to Read First

1. `README.md` — Project overview and architecture
2. `src/main.py` — App factory, exception handlers, middleware
3. `src/domain/exceptions.py` — Custom exception hierarchy
4. `src/core/config.py` — All configuration / env vars
5. `docs/rbac_permissions.md` — RBAC permission matrix
6. `docs/analysys_plan.md` — Original project requirements
```

---

### Step 3.5 — Create `gotchas.md`

**File:** `gotchas.md` (project root)

```markdown
# Gotchas — Known Issues & Workarounds

> Living document. Add new entries at the top.

---

### `pyproject.toml` says `requires-python >= 3.14` but Dockerfile uses `python:3.12-slim`

**Problem:** Python 3.14 slim images may not be available or stable on all platforms.

**Workaround:** Use `python:3.12-slim` in Docker. The app runs fine on 3.12+.
Update to `python:3.14-slim` when it reaches GA and has stable slim images.

**Date:** 2025-07-11

---

### Tests use aiosqlite (SQLite) but production uses asyncpg (PostgreSQL)

**Problem:** Some PostgreSQL-specific behavior (e.g., `ON CONFLICT`, array types,
`JSONB`) may not be caught by SQLite-based tests.

**Workaround:** Use `docker-compose.test.yml` to run tests against a real PostgreSQL
instance for integration testing. Keep aiosqlite for fast local unit tests.

**Date:** 2025-07-11

---

### `GET /users` endpoint was removed but 3 tests still reference it

**Problem:** 3 pre-existing test failures for the removed `GET /users` endpoint.

**Workaround:** These tests should be deleted or updated. They are known failures
and do not affect the 108 passing tests.

**Date:** 2025-07-11

---

### Railway `$PORT` environment variable

**Problem:** Railway injects a `PORT` env var that may differ from the default 8000.
If the app doesn't bind to `$PORT`, Railway's health check fails and the deploy rolls back.

**Workaround:** `Dockerfile` CMD uses `${PORT:-8000}`. `railway.toml` `startCommand`
explicitly references `$PORT`. `Settings` class has `PORT: int = 8000` as fallback.

**Date:** 2025-07-11

---

### `docker-entrypoint.sh` must be LF line endings (not CRLF)

**Problem:** If the entrypoint script has Windows-style line endings, the container
fails with `/bin/bash^M: bad interpreter`.

**Workaround:** Ensure `.gitattributes` forces LF for `.sh` files:
```
*.sh text eol=lf
```

**Date:** 2025-07-11
```

---

### Step 3.6 — Create `.gitattributes`

**File:** `.gitattributes` (project root)

```gitattributes
# Force LF line endings for shell scripts (Docker entrypoint)
*.sh text eol=lf

# Force LF for YAML (Docker Compose, GitHub Actions)
*.yml text eol=lf
*.yaml text eol=lf

# Force LF for TOML (railway.toml, pyproject.toml)
*.toml text eol=lf
```

---

### Step 3.7 — Create API Changelog

**File:** `docs/api/CHANGELOG.md`

```markdown
# API Changelog

All notable changes to the API surface are documented here.
This project follows [Semantic Versioning](https://semver.org/).

---

## [0.2.0] — 2025-07-11

### Changed

- **`GET /health`** — Response now includes `database` field (`"connected"` |
  `"disconnected"` | `"unknown"`). The `status` field can now be `"degraded"`
  when the database is unreachable (previously only `"healthy"`).

### Added

- Docker health check uses `GET /health` endpoint.
- Railway deployment configured with `healthcheckPath = "/health"`.

### Infrastructure (non-API)

- Added `Dockerfile` — multi-stage build with `python:3.12-slim`, non-root user.
- Added `.dockerignore` — excludes secrets, tests, IDE files from build context.
- Added `docker-entrypoint.sh` — runs Alembic migrations before server start.
- Added `docker-compose.yml` — local dev stack (app + PostgreSQL 16 + Redis 7).
- Added `docker-compose.test.yml` — test runner with Dockerized PostgreSQL.
- Added `railway.toml` — Railway deployment config (Dockerfile builder).
- Added `.github/workflows/ci.yml` — CI pipeline (lint → test → Docker build).
- Added `.github/copilot-instructions.md` — AI assistant project context.
- Added `.claude/CLAUDE.md` — Claude agent instructions.
- Added `gotchas.md` — known issues and workarounds.
- Added `.gitattributes` — LF line endings for scripts/configs.

---

## [0.1.0] — 2025-XX-XX (Initial Release)

### Added

- JWT authentication (access + refresh tokens).
- User registration and profile management.
- Project CRUD with role-based access (Admin / Manager / Member).
- Task CRUD with filtering, sorting, pagination.
- Task comments.
- WebSocket real-time notifications.
- RBAC permission system.
- Custom domain exception hierarchy with global handlers.
```

---

### Step 3.8 — Day 3 verification gate (FINAL)

```bash
# ── Lint ──────────────────────────────────────────
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# ── Tests (host) ─────────────────────────────────
uv run pytest --tb=short -q

# ── Docker build ─────────────────────────────────
docker build -t task-manager-api:final .

# ── Image size ───────────────────────────────────
docker images task-manager-api:final --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# ── Docker Compose smoke test ────────────────────
docker compose up -d --build
sleep 10  # Wait for migrations + health checks
curl -sf http://localhost:8000/health | python -m json.tool
docker compose down

# ── Verify all new files exist ───────────────────
for f in \
    Dockerfile \
    .dockerignore \
    docker-entrypoint.sh \
    docker-compose.yml \
    docker-compose.test.yml \
    railway.toml \
    .gitattributes \
    gotchas.md \
    .claude/CLAUDE.md \
    .github/copilot-instructions.md \
    .github/workflows/ci.yml \
    docs/api/CHANGELOG.md \
    tests/test_health.py; do
  [ -f "$f" ] && echo "✅ $f" || echo "❌ MISSING: $f"
done

# ── Final commit ─────────────────────────────────
git add -A
git commit -m "feat(devops): complete Docker + Compose + Railway + CI/CD setup

Day 1: Dockerfile (multi-stage), .dockerignore, entrypoint, enhanced /health
Day 2: docker-compose.yml (app+PG+Redis), railway.toml, Settings.PORT
Day 3: CI/CD workflow, copilot-instructions, CLAUDE.md, gotchas, changelog

- All 108+ tests pass
- Image size < 250 MB
- Non-root container user
- Alembic migrations run at container startup
- GitHub Actions: lint → test → docker build
- Railway: Dockerfile builder with health check"
```

---

## 7. Post-Implementation Checklist

```
[ ] All files from §9 File Manifest exist
[ ] uv run ruff check src/ tests/ — 0 errors
[ ] uv run pytest --tb=short -q — 108+ tests pass
[ ] docker build completes without errors
[ ] docker compose up -d --build — all 3 services healthy
[ ] curl localhost:8000/health — returns {"status": "healthy", ...}
[ ] docker compose down — clean shutdown
[ ] .github/workflows/ci.yml — valid YAML (yamllint or GH Actions dry-run)
[ ] gotchas.md — at least 5 entries documented
[ ] .claude/CLAUDE.md — accurate project layout
[ ] .github/copilot-instructions.md — accurate commands and conventions
[ ] docs/api/CHANGELOG.md — documents /health changes
[ ] railway.toml — healthcheckPath set
[ ] .gitattributes — LF for .sh, .yml, .toml
[ ] No secrets in any committed file (grep -r "SECRET" --include="*.py" .)
[ ] Git history is clean (no WIP commits)
```

---

## 8. API Changelog

See `docs/api/CHANGELOG.md` (created in Step 3.7).

**Summary of API-surface changes:**

| Endpoint | Change | Before | After |
|----------|--------|--------|-------|
| `GET /health` | Added `database` field | `{"status": "healthy", "version": "0.1.0"}` | `{"status": "healthy", "version": "0.1.0", "database": "connected"}` |
| `GET /health` | `status` can be `"degraded"` | Only `"healthy"` | `"healthy"` or `"degraded"` |

No other API endpoints were added, modified, or removed.

---

## 9. File Manifest

All files created or modified in this plan:

| File | Action | Day | Description |
|------|--------|-----|-------------|
| `.dockerignore` | **CREATE** | 1 | Build context exclusions |
| `Dockerfile` | **CREATE** | 1 | Multi-stage production build |
| `docker-entrypoint.sh` | **CREATE** | 1 | Migration runner + server start |
| `src/schemas/common.py` | **MODIFY** | 1 | Add `database` field to `HealthResponse` |
| `src/main.py` | **MODIFY** | 1 | Enhanced `/health` with DB check |
| `tests/test_health.py` | **CREATE** | 1 | Health endpoint tests |
| `docker-compose.yml` | **CREATE** | 2 | Local dev stack (app + PG + Redis) |
| `docker-compose.test.yml` | **CREATE** | 2 | Dockerized test runner |
| `railway.toml` | **CREATE** | 2 | Railway deployment config |
| `src/core/config.py` | **MODIFY** | 2 | Add `PORT` setting |
| `.github/workflows/ci.yml` | **CREATE** | 3 | CI pipeline (lint → test → build) |
| `.github/copilot-instructions.md` | **CREATE** | 3 | Copilot AI assistant context |
| `.claude/CLAUDE.md` | **CREATE** | 3 | Claude agent instructions |
| `gotchas.md` | **CREATE** | 3 | Known issues & workarounds |
| `.gitattributes` | **CREATE** | 3 | Line ending normalization |
| `docs/api/CHANGELOG.md` | **CREATE** | 3 | API changelog |

**Total: 16 files (11 new, 5 modified)**

---

## Appendix A — Execution Order for AI Agent

The agent should execute steps in this exact order. Each step has a `GATE` —
do not proceed past a gate until all checks pass.

```
1.1  Create .dockerignore
1.2  Create Dockerfile
1.3  Create docker-entrypoint.sh
1.4  Build and test Docker image               ← GATE: image builds, < 250 MB
1.5  Enhance /health endpoint
1.6  Add health endpoint tests
1.7  Day 1 gate                                 ← GATE: all tests pass, lint clean

2.1  Create docker-compose.yml
2.2  Create docker-compose.test.yml
2.3  Verify Docker Compose locally              ← GATE: stack starts, health OK
2.4  Railway setup (MANUAL)
2.5  Create railway.toml
2.6  Update Settings for PORT
2.7  Railway env vars (MANUAL)
2.8  Deploy to Railway (MANUAL)
2.9  Day 2 gate                                 ← GATE: local + Railway healthy

3.1  Optimize Dockerfile
3.2  Create GitHub Actions CI workflow
3.3  Create .github/copilot-instructions.md
3.4  Create .claude/CLAUDE.md
3.5  Create gotchas.md
3.6  Create .gitattributes
3.7  Create docs/api/CHANGELOG.md
3.8  Day 3 final gate                           ← GATE: everything passes
```

---

*End of execution plan.*
