# CLAUDE.md — Agent Instructions

## About This Project

Collaborative Project & Task Management API — a Trello/Jira-like backend built
with FastAPI. See `README.md` for full documentation.

## Repository Layout

```
fast_api_practice/
├── src/
│   ├── api/v1/           # Route handlers (NO try/except — raise domain exceptions)
│   ├── core/config.py    # Settings via pydantic-settings (env-driven)
│   ├── domain/
│   │   ├── exceptions.py # DomainError → NotFoundError, AuthorizationError…
│   │   ├── models/       # SQLAlchemy async ORM models
│   │   └── services/     # Business logic (raise, never catch, domain exceptions)
│   ├── infrastructure/   # DB connection, logging, email
│   ├── schemas/          # Pydantic DTOs
│   ├── websockets/       # Real-time notifications
│   └── main.py           # App factory + global exception handlers
├── tests/                # pytest-asyncio; aiosqlite in-memory DB
├── alembic/versions/     # Database migrations
├── Dockerfile            # Multi-stage: python:3.14-slim builder + runtime
├── docker-compose.yml    # Local stack: app + PostgreSQL 16 + Redis 7
├── docker-compose.test.yml  # Test runner (Dockerised PostgreSQL)
├── docker-entrypoint.sh  # Runs migrations then starts uvicorn
├── railway.toml          # Railway deployment (Dockerfile builder)
├── .github/workflows/    # CI: lint → test → docker build
├── gotchas.md            # Known issues & workarounds (read before debugging)
└── docs/api/CHANGELOG.md # API surface changelog
```

## Critical Rules

1. **NEVER add try/except in route handlers.** Services raise domain exceptions;
   `main.py` global handlers catch them.
2. **ALWAYS use `python -m uvicorn` and `python -m alembic`** — never bare script
   names. Venv script shebangs break in multi-stage Docker builds.
3. **ALWAYS run after any change:**
   ```bash
   uv run ruff check src/ tests/
   uv run ruff format src/ tests/
   uv run pytest --tb=short -q
   ```
4. **Conventional commits:** `feat:`, `fix:`, `docs:`, `ci:`, `refactor:`, `chore:`
5. **Environment variables:** All config via `.env`. NEVER hardcode secrets.
6. **Migrations:** After model changes, run:
   `uv run alembic revision --autogenerate -m "description"` then review the file.

## Before Every Commit

```bash
uv run ruff check src/ tests/          # Must pass (0 errors)
uv run ruff format --check src/ tests/ # Must pass
uv run pytest --tb=short -q            # Must pass (117+ tests, 3 known failures OK)
```

## Key Files to Read First

1. `README.md` — Project overview and quick-start
2. `src/main.py` — App factory, exception handlers, middleware wiring
3. `src/domain/exceptions.py` — Custom exception hierarchy
4. `src/core/config.py` — All settings / env vars (including `PORT`)
5. `gotchas.md` — Known issues (especially Docker multi-stage gotchas)
6. `docs/rbac_permissions.md` — RBAC permission matrix

## Known Gotchas (summary)

See `gotchas.md` for full entries. Critical ones:

- `uv sync` in Docker builder creates venv scripts with broken shebangs →
  always use `python -m alembic` / `python -m uvicorn`
- `ALTER TYPE ADD VALUE` in PostgreSQL cannot be used in the same transaction
  as DML referencing the new value — commit it first
- Multiple Alembic heads crash migrations → run `uv run alembic heads` to check
- `python:3.14-slim` required (not 3.12) — `pyproject.toml` sets `requires-python >= 3.14`
