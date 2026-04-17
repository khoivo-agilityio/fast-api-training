# Copilot Instructions — Collaborative Task Manager API

## Project Overview

FastAPI-based Trello/Jira-like backend with JWT auth, RBAC, async PostgreSQL,
WebSocket notifications, and Docker/Railway deployment.

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.14, FastAPI, Uvicorn |
| Database | PostgreSQL 16, SQLAlchemy 2.0 async, asyncpg |
| Auth | PyJWT + bcrypt (access + refresh tokens) |
| Migrations | Alembic |
| Package manager | uv (pyproject.toml + uv.lock) |
| Linting | Ruff |
| Testing | pytest + pytest-asyncio + httpx + aiosqlite |
| Containerisation | Docker multi-stage, Docker Compose |
| Deployment | Railway (Dockerfile builder) |
| CI/CD | GitHub Actions |

## Architecture

```
src/
├── api/v1/          # Route handlers — thin, NO try/except, NO business logic
├── core/            # Settings (pydantic-settings), security utils
├── domain/
│   ├── exceptions.py  # DomainError hierarchy (NotFoundError, AuthorizationError…)
│   ├── models/        # SQLAlchemy async ORM models
│   └── services/      # Business logic; raise domain exceptions
├── infrastructure/    # DB connection, logging, email
├── schemas/           # Pydantic request/response DTOs
├── websockets/        # Real-time notification router
└── main.py            # App factory, global exception handlers, middleware
```

## Key Conventions

1. **Exception handling:** Services raise domain exceptions; global handlers in
   `main.py` convert them to JSON. Route handlers have **NO** `try/except`.
2. **Dependency injection:** Always use `Depends()` for sessions, auth, services.
3. **Async everywhere:** All DB operations use `async/await`.
4. **Tests:** Use `aiosqlite` in-memory DB — never a real PostgreSQL instance.
5. **Commits:** Conventional commits — `feat:`, `fix:`, `docs:`, `ci:`, `refactor:`.
6. **Docker:** `python -m uvicorn` and `python -m alembic` (never bare scripts —
   venv script shebangs break in multi-stage builds).
7. **Environment:** All config via env vars. Never hardcode secrets.

## Common Commands

```bash
uv run pytest --tb=short -q              # Run tests
uv run ruff check src/ tests/            # Lint
uv run ruff format src/ tests/           # Format
docker compose up -d --build             # Start local stack (app + PG + Redis)
docker compose down                      # Stop local stack
docker compose logs app --tail=50        # App logs
uv run alembic upgrade head              # Run migrations (host)
uv run alembic revision --autogenerate -m "description"   # New migration
```

## Gotchas

See `gotchas.md` in the project root for all known issues and workarounds.
The most critical Docker gotcha: **always use `python -m <script>`** instead of
bare venv scripts (`uvicorn`, `alembic`) — their shebangs break in multi-stage builds.
