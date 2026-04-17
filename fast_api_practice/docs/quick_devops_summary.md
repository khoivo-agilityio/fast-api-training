# Quick DevOps Summary — 1-Day Compressed Execution Guide

> **Source:** [KhoiVo] DevOps Training Plan (3 days → distilled to ~6 hours of focused work)  
> **Project:** Collaborative Project & Task Management API (FastAPI + PostgreSQL + Redis)  
> **Goal:** 20% of the actions that deliver 80% of the value — working containers, deployed app, CI/CD gate.

---

## Table of Contents

1. [Core Workflow (The 80/20 Map)](#1-core-workflow-the-8020-map)
2. [Daily Timeline (6-Hour Schedule)](#2-daily-timeline-6-hour-schedule)
3. [Manual Action Items](#3-manual-action-items)
4. [Agent-Assisted Plan + Prompts](#4-agent-assisted-plan--prompts)

---

## 1. Core Workflow (The 80/20 Map)

These are the **8 concepts** that underpin everything else. Master them and the rest is detail-lookup.

| # | Concept | What You Actually Need to Know | Skip / Skim |
|---|---------|-------------------------------|-------------|
| 1 | **Dockerfile (multi-stage)** | `FROM base AS builder` → `FROM slim AS runtime`, `COPY --from=builder`, `ENTRYPOINT` vs `CMD` | Single-stage builds |
| 2 | **`.dockerignore`** | Exclude `__pycache__`, `.venv`, `.git`, `*.pyc` — keeps build context small and cache clean | Deep union-FS theory |
| 3 | **`docker compose up -d`** | `services`, `depends_on` + `healthcheck`, named `volumes`, `environment` / `env_file` | Swarm mode |
| 4 | **Health checks** | `test: ["CMD", "curl", "-f", "http://localhost:8000/health"]`, `interval/timeout/retries` — compose waits for green before starting dependents | Overlay networks |
| 5 | **Entrypoint script** | Run migrations *then* start server: `alembic upgrade head && exec uvicorn …` — `exec` hands PID 1 to uvicorn so SIGTERM works | Init systems (s6, supervisord) |
| 6 | **Railway `railway.toml`** | `[build] builder = "DOCKERFILE"` + `[deploy] startCommand` + `healthcheckPath` — Railway reads this file at deploy time | Nixpacks internals |
| 7 | **Environment variables in Railway** | Dashboard → Variables tab; reference another service: `${{Postgres.DATABASE_URL}}`; Railway auto-injects `PORT` | Secrets manager integrations |
| 8 | **GitHub Actions CI** | `on: push` → lint → test (postgres service container) → docker build; fail-fast prevents bad code reaching Railway | Self-hosted runners |

### Mental Model: The Deployment Path

```
Local code
  │
  ├─► docker build → docker compose up   (Day 1–2: local confidence)
  │
  └─► git push → GitHub Actions CI       (Day 3: automated gate)
            │
            └─► Railway auto-deploy      (on main branch green)
                      │
                      └─► railway.toml → Docker build → entrypoint.sh
                                                  │
                                                  ├─► alembic upgrade head
                                                  └─► uvicorn (PID 1)
```

---

## 2. Daily Timeline (6-Hour Schedule)

### Hour 1 — Containerize (Dockerfile)

**Goal:** `docker run` your app locally with a working `/health` endpoint.

```bash
# Build
docker build -t myapp:local .

# Run (pass DB URL as env var)
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  myapp:local

# Verify
curl http://localhost:8000/health
# → {"status":"healthy","database":"connected"}
```

**Key files:** `Dockerfile`, `.dockerignore`, `docker-entrypoint.sh`

**Gotcha #1:** Always use `exec` in the entrypoint — without it, your shell is PID 1 and SIGTERM never reaches the app.

---

### Hour 2 — Multi-Container Stack (Docker Compose)

**Goal:** One command brings up app + Postgres + Redis; all healthy.

```bash
docker compose up -d
docker compose ps          # all services "healthy", not just "running"
docker compose logs app -f # watch migration + startup
curl http://localhost:8000/health
```

**Key file:** `docker-compose.yml`

```yaml
# Minimum viable pattern
services:
  app:
    build: .
    ports: ["8000:8000"]
    depends_on:
      db:
        condition: service_healthy   # ← waits for DB healthcheck to pass
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/app

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

**Gotcha #2:** `depends_on` with no `condition` does NOT wait for the DB to be ready — it only waits for the container to start. Use `condition: service_healthy`.

---

### Hour 3 — Deploy to Railway (First Deploy)

**Goal:** Live URL for your app on Railway, reading from a managed Postgres.

**Steps (manual — see Section 3 for detail):**
1. Push your repo to GitHub
2. Create Railway project → "Deploy from GitHub repo"
3. Add PostgreSQL service from Railway template
4. Copy `DATABASE_URL` variable reference into your app service
5. Add `railway.toml` to your repo and push

**Key file:** `railway.toml`
```toml
[build]
builder = "DOCKERFILE"

[deploy]
startCommand = "./docker-entrypoint.sh"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Gotcha #3:** Railway injects `PORT` at runtime. Your app **must** bind to `0.0.0.0:$PORT`, not a hardcoded port. In the entrypoint: `--port "${PORT:-8000}"`.

---

### Hour 4 — Config as Code + Variables

**Goal:** No manual clicking in Railway dashboard; everything reproducible from the repo.

**Checklist:**
- [ ] `railway.toml` committed — build/deploy config lives in git
- [ ] All secrets in Railway Variables tab (never in `railway.toml`)
- [ ] Reference Railway-managed DB: `DATABASE_URL=${{Postgres.DATABASE_URL}}`
- [ ] `PORT` is read from environment (Railway sets it; entrypoint uses `${PORT:-8000}`)

**Gotcha #4:** Railway's free tier sleeps after inactivity. For health checks to pass at deploy time, set `healthcheckTimeout` ≥ 30s to survive cold-start DB connection.

---

### Hour 5 — CI/CD with GitHub Actions

**Goal:** Every push to `main` runs lint → test → docker build; Railway only deploys green code.

**Key file:** `.github/workflows/ci.yml` (abbreviated)

```yaml
on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv run ruff check .

  test:
    needs: lint
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env: { POSTGRES_PASSWORD: postgres, POSTGRES_DB: testdb }
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv run pytest

  docker-build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v6
        with:
          push: false
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**Gotcha #5:** GitHub Actions postgres service container is accessible at `localhost`, not `postgres` — set `DATABASE_URL` in the test job's `env:` accordingly.

---

### Hour 6 — Verify End-to-End + Production Checklist

**Run locally:**
```bash
docker compose down -v && docker compose up -d
docker compose ps                    # all healthy
docker compose exec app python -m pytest tests/test_health.py -v
```

**Production checklist (from Railway docs, adapted):**

| Item | Done? |
|------|-------|
| App binds to `$PORT` | ☐ |
| `DATABASE_URL` from Railway variable reference | ☐ |
| `/health` endpoint returns 200 + DB check | ☐ |
| `healthcheckPath` in `railway.toml` | ☐ |
| Migrations run in entrypoint (not in Dockerfile) | ☐ |
| No secrets in `Dockerfile` or `railway.toml` | ☐ |
| CI gate blocks merge on failure | ☐ |
| `.dockerignore` excludes `.venv`, `__pycache__`, `.git` | ☐ |

---

## 3. Manual Action Items

These **require a human** — browser clicks, account setup, or local secrets. An AI agent cannot do these for you.

### One-Time Setup

1. **Install Docker Desktop** (Windows/macOS) or Docker Engine (Linux)  
   → https://docs.docker.com/get-started/get-docker/

2. **Create a Railway account**  
   → https://railway.com — free trial, no credit card required initially

3. **Install the Railway CLI**
   ```bash
   # macOS
   brew install railway
   # or via npm
   npm install -g @railway/cli
   ```

4. **Authenticate Railway CLI**
   ```bash
   railway login
   ```

5. **Connect GitHub to Railway**  
   → Railway Dashboard → Settings → Integrations → GitHub → Authorize

### Per-Project Steps (Railway Dashboard)

6. **Create a new Railway project**  
   → Dashboard → New Project → "Deploy from GitHub repo" → select your repo

7. **Add PostgreSQL service**  
   → In your Railway project → New Service → Database → PostgreSQL

8. **Add Redis service** (if needed)  
   → New Service → Database → Redis

9. **Wire DATABASE_URL into your app service**  
   → App service → Variables → Add:  
   `DATABASE_URL = ${{Postgres.DATABASE_URL}}`

10. **Set any app-specific secrets**  
    → App service → Variables → Add `SECRET_KEY`, `JWT_SECRET`, etc.  
    ⚠️ Never commit secrets — set them only in the Railway dashboard.

11. **Trigger first deploy / verify**  
    → Deployments tab → watch build logs → click the generated URL  
    → `curl https://your-app.railway.app/health`

### GitHub Secrets (for CI pushing to a registry)

12. If you add a `docker push` step to CI, add to GitHub repo Settings → Secrets:  
    - `DOCKERHUB_USERNAME`
    - `DOCKERHUB_TOKEN`
    *(Not needed if CI only builds without pushing.)*

---

## 4. Agent-Assisted Plan + Prompts

Use these prompts with GitHub Copilot, Cursor, or any coding AI agent. Each prompt maps to a specific deliverable.

---

### Prompt A — Generate the Dockerfile

```
I have a FastAPI app in `src/main.py` using:
- Python 3.12
- uv for package management (pyproject.toml + uv.lock)
- PostgreSQL via asyncpg
- Alembic for migrations

Generate a production-ready multi-stage Dockerfile:
1. Build stage: install deps with uv into /app/.venv
2. Runtime stage: python:3.12-slim, copy .venv + src, run as non-root user
3. ENTRYPOINT pointing to docker-entrypoint.sh (do NOT put CMD)
4. Include a .dockerignore that excludes .venv, __pycache__, .git, *.pyc, tests/

Also generate docker-entrypoint.sh that:
- Runs `python -m alembic upgrade head`
- Then `exec python -m uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"`
- Uses `set -euo pipefail`
```

---

### Prompt B — Generate docker-compose.yml

```
Generate a docker-compose.yml for local development with:
- Service `app`: builds from local Dockerfile, port 8000, depends on db and redis being healthy
- Service `db`: postgres:16-alpine, named volume `pgdata`, healthcheck using pg_isready
- Service `redis`: redis:7-alpine, named volume `redisdata`, healthcheck using redis-cli ping
- All services on a custom bridge network `appnet`
- Environment variables for DATABASE_URL and REDIS_URL wired from service hostnames
- Restart policy: unless-stopped for db and redis

Also generate a docker-compose.test.yml override that:
- Overrides `app` to run `python -m pytest` instead of the entrypoint
- Does NOT expose port 8000
```

---

### Prompt C — Generate railway.toml

```
Generate a railway.toml for a FastAPI app with:
- Builder: DOCKERFILE
- startCommand: ./docker-entrypoint.sh
- healthcheckPath: /health
- healthcheckTimeout: 30 seconds
- restartPolicy: ON_FAILURE, max 3 retries

The app reads PORT from environment (Railway injects it).
```

---

### Prompt D — Add /health endpoint with DB check

```
I have a FastAPI app. Add a `/health` endpoint that:
1. Returns {"status": "healthy", "database": "connected"} on success with HTTP 200
2. Returns {"status": "unhealthy", "database": "disconnected"} with HTTP 503 if DB is unreachable
3. Use a Pydantic response schema `HealthResponse` with fields: status (str), database (str)
4. The DB check should execute a simple `SELECT 1` via SQLAlchemy async session
5. Add to `tests/test_health.py`: tests for healthy state, DB failure (mock the session), and correct status codes
```

---

### Prompt E — Generate GitHub Actions CI workflow

```
Generate a GitHub Actions workflow `.github/workflows/ci.yml` that:

Jobs (in order, each depends on previous):
1. `lint`: checkout → setup uv (astral-sh/setup-uv@v6) → run ruff check
2. `test`: 
   - uses postgres:16-alpine as a service container (with healthcheck)
   - checkout → setup uv → run pytest
   - sets DATABASE_URL env var pointing to localhost postgres
3. `docker-build`:
   - checkout → docker/setup-buildx-action@v3
   - build with docker/build-push-action@v6, push: false
   - use GitHub Actions cache (type=gha)

Trigger: push to main, and pull_request to main.
Python version: 3.12
```

---

### Prompt F — Fix Alembic enum migration (PostgreSQL-specific)

```
I have an Alembic migration that adds values to a PostgreSQL enum type using
`ALTER TYPE my_enum ADD VALUE IF NOT EXISTS 'new_value'`.

This fails because PostgreSQL cannot ADD VALUE inside a transaction.

Fix the migration's `upgrade()` function to:
1. Use `op.get_bind()` to get the raw connection
2. Execute COMMIT before each ALTER TYPE statement
3. Execute BEGIN after all ALTER TYPE statements to restore transactional context
4. Use `sqlalchemy.text` for the raw SQL strings
5. Keep any subsequent DML (INSERT, UPDATE) inside the restored transaction

Show the complete corrected upgrade() function.
```

---

### Prompt G — Production readiness review

```
Review these files for production readiness before deploying to Railway:
- Dockerfile
- docker-entrypoint.sh
- railway.toml
- src/core/config.py (Settings class)

Check for:
1. App correctly reads PORT from environment
2. No hardcoded secrets or connection strings
3. ENTRYPOINT uses exec so PID 1 is the app process
4. Migrations run before app starts
5. Health check endpoint exists and checks DB connectivity
6. Non-root user in Docker runtime stage
7. .dockerignore excludes development artifacts

List any issues found and provide corrected code.
```

---

> **Note:** Prompts A–G are incremental. You can run them in order on a blank project and arrive at the same infrastructure produced by this 3-day training plan in under 2 hours. Always review generated code before committing — check that secrets are not embedded, that `exec` is present in entrypoints, and that CI tests actually connect to the service container.
