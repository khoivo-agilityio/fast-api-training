# Collaborative Task Manager API

A **Trello/Jira-like** project and task management backend built with
**FastAPI**, **async SQLAlchemy**, and **PostgreSQL**, following Clean Architecture principles.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI (Python 3.12+) |
| ORM | SQLAlchemy 2 (async) |
| Database | PostgreSQL (asyncpg driver) |
| Migrations | Alembic |
| Auth | JWT (PyJWT) + bcrypt |
| Validation | Pydantic v2 |
| Logging | structlog |
| Testing | pytest-asyncio + httpx + aiosqlite |
| Packaging | uv |

---

## Architecture

```
src/
├── core/               # Config, security, RBAC permissions
├── domain/
│   ├── entities/       # Pure Python dataclasses (no ORM)
│   ├── repositories/   # Abstract base interfaces (ABCs)
│   └── services/       # Business logic
├── infrastructure/
│   ├── database/       # SQLAlchemy models, async engine, repo implementations
│   └── logging/        # structlog setup
├── schemas/            # Pydantic request/response models
├── api/
│   ├── middleware.py   # Request-ID + timing middleware
│   ├── dependencies.py # FastAPI Depends factories
│   └── v1/             # Route handlers
└── main.py             # App factory + lifespan
```

---

## Features

### Authentication
- `POST /api/v1/auth/register` — register a new user
- `POST /api/v1/auth/login` — login, receive access + refresh JWT pair
- `POST /api/v1/auth/refresh` — rotate tokens via refresh token

### Users
- `GET  /api/v1/users/me` — get own profile
- `PATCH /api/v1/users/me` — update name / email / password
- `GET  /api/v1/users` — list all users **(admin only)**

### Projects
- `POST   /api/v1/projects` — create project (auto-adds creator as manager)
- `GET    /api/v1/projects` — list projects the current user belongs to
- `GET    /api/v1/projects/{id}` — get project details
- `PATCH  /api/v1/projects/{id}` — update name/description (owner or manager)
- `DELETE /api/v1/projects/{id}` — delete project (owner only)

### Project Members
- `POST   /api/v1/projects/{id}/members` — add member (manager+)
- `GET    /api/v1/projects/{id}/members` — list members
- `PATCH  /api/v1/projects/{id}/members/{uid}` — change member role (manager+)
- `DELETE /api/v1/projects/{id}/members/{uid}` — remove member (manager+)

### Tasks
- `POST   /api/v1/projects/{id}/tasks` — create task (project members)
- `GET    /api/v1/projects/{id}/tasks` — list tasks (optional `status`/`assignee_id` filters)
- `GET    /api/v1/projects/{id}/tasks/{tid}` — get task
- `PATCH  /api/v1/projects/{id}/tasks/{tid}` — update task
- `DELETE /api/v1/projects/{id}/tasks/{tid}` — delete task

### Comments
- `POST   /api/v1/tasks/{tid}/comments` — add comment (project members)
- `GET    /api/v1/tasks/{tid}/comments` — list comments
- `PATCH  /api/v1/tasks/{tid}/comments/{cid}` — edit own comment
- `DELETE /api/v1/tasks/{tid}/comments/{cid}` — delete own comment

---

## RBAC Roles

| Role | Scope | Capabilities |
|---|---|---|
| `admin` | Global | Everything, including listing all users |
| `manager` | Project | Create/update/delete projects, manage members |
| `member` | Project | Read projects, create/update tasks & comments |

Project-level roles (`ProjectMemberRole.MANAGER` / `MEMBER`) are separate from
global user roles and are set per-project via the members API.

---

## Middleware

Every response includes:
- `X-Request-ID` — unique UUID4 per request (also bound in structlog context)
- `X-Process-Time` — request duration in milliseconds
- CORS headers (configurable via `CORS_ORIGINS` in `.env`)

---

## Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL running locally
- [uv](https://docs.astral.sh/uv/) installed

### Setup

```bash
# 1. Install dependencies
uv sync

# 2. Copy env and configure
cp .env.example .env
# Edit DATABASE_URL, JWT_SECRET_KEY, etc.

# 3. Run migrations
uv run alembic upgrade head

# 4. Start the server
uv run uvicorn main:app --reload
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | Dev database |
| `DATABASE_URL_TEST` | `postgresql+asyncpg://...` | Test database |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `DEBUG` | `True` | Enables coloured console logs |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |

---

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# With coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run a specific file
uv run pytest tests/test_permissions.py -v
```

**Current coverage: 93.55%** (target: ≥80%)

### Test Files

| File | What it tests |
|---|---|
| `test_auth.py` | Registration, login, token refresh (19 tests) |
| `test_users.py` | Profile endpoints (6 tests) |
| `test_projects.py` | Project CRUD + member management (18 tests) |
| `test_tasks.py` | Task CRUD + filters (13 tests) |
| `test_comments.py` | Comment CRUD + ownership (9 tests) |
| `test_schemas.py` | Pydantic schema validation (20 tests) |
| `test_permissions.py` | RBAC + middleware headers (11 tests) |

---

## Interactive Docs

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health
