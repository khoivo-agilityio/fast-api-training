# Collaborative Task Manager API

A **Trello/Jira-like** project & task management REST API built with FastAPI, async SQLAlchemy, and PostgreSQL. Features JWT authentication, role-based access control, real-time WebSocket notifications, and background email simulations.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) — Python 3.12+ |
| Database | PostgreSQL 17 (async via `asyncpg`) |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Auth | PyJWT + passlib[bcrypt] |
| Validation | Pydantic v2 |
| Logging | structlog (JSON) |
| Testing | pytest + httpx + starlette TestClient |
| Linting | Ruff |
| Package manager | uv |

---

## Architecture

```
fast_api_practice/
├── alembic/                          # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── src/
│   ├── main.py                       # App factory + lifespan
│   ├── core/                         # Cross-cutting concerns
│   │   ├── config.py                 # Settings (pydantic-settings + .env)
│   │   ├── security.py               # Password hashing, JWT create/decode
│   │   └── permissions.py            # RBAC permission checker
│   ├── domain/                    
│   │   ├── entities/              
│   │   ├── repositories/             # Abstract repository interfaces (ABCs)
│   │   └── services/                 # Business logic layer
│   ├── infrastructure/               # Framework-specific implementations
│   │   ├── database/
│   │   ├── logging/
│   │   └── background.py             # Email notification simulators
│   ├── schemas/                      # Pydantic request/response schemas
│   ├── api/                          # Route layer
│   │   ├── dependencies.py          
│   │   └── v1/
│   └── websockets/
├── tests/
├── alembic.ini
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
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

### Projects
- `POST   /api/v1/projects` — create project (auto-adds creator as admin)
- `GET    /api/v1/projects` — list projects the current user belongs to
- `GET    /api/v1/projects/{id}` — get project details
- `PATCH  /api/v1/projects/{id}` — update name/description (owner )
- `DELETE /api/v1/projects/{id}` — delete project (owner only)

### Project Members
- `POST   /api/v1/projects/{id}/members` — add member (admin)
- `GET    /api/v1/projects/{id}/members` — list members
- `PATCH  /api/v1/projects/{id}/members/{uid}` — change member role (admin)
- `DELETE /api/v1/projects/{id}/members/{uid}` — remove member (admin)

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
| `admin` | Project | Create/update/delete projects, manage members |
| `member` | Project | Read projects, create/update tasks & comments |

---

## Middleware

Every response includes:
- `X-Request-ID` — unique UUID4 per request (also bound in structlog context)
- `X-Process-Time` — request duration in milliseconds

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
uv run uvicorn src.main:app --reload
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | Async PostgreSQL URL (`postgresql+asyncpg://...`) |
| `DATABASE_URL_TEST` | — | Test database URL |
| `JWT_SECRET_KEY` | — | JWT signing secret — **change in production** |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `DEBUG` | `false` | Enables SQL echo + debug logging |
| `SMTP_ENABLED` | `false` | Send real emails when `true` |
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP port |
| `SMTP_USERNAME` | — | SMTP login username |
| `SMTP_PASSWORD` | — | SMTP app password |
| `SMTP_FROM` | — | Sender email address |

---

## Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# With coverage report
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run a specific file
uv run pytest tests/test_permissions.py -v

# With HTML test report + coverage HTML
uv run pytest tests/ -v \
  --cov=src \
  --cov-report=html:reports/coverage \
  --html=reports/report.html \
  --self-contained-html

# Open reports
open reports/report.html        # test results
open reports/coverage/index.html # coverage details
```

**Current coverage: 88.00%** (target: ≥80%)

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
