# Task Manager API

A production-ready REST API built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**, following clean architecture principles. Features JWT authentication, structured logging, Alembic migrations, and comprehensive test coverage.

---

## ✨ Features

- 🔐 **JWT Authentication** — register, login, token-based access
- ✅ **Task CRUD** — create, read, update, delete tasks with filtering & pagination
- 🗃️ **PostgreSQL** — production-grade database with Alembic migrations
- 🏗️ **Clean Architecture** — domain, infrastructure, and API layers separated
- 📋 **Structured Logging** — `structlog` with JSON (prod) and console (dev) formats
- 🧪 **169 Tests** — unit + API integration tests at 87% coverage
- ⚙️ **Environment-based Config** — all settings via `.env` using Pydantic Settings

---

## 🗂️ Project Structure

```
fast_api_big_exercise/
├── alembic/                        # Database migrations
│   ├── env.py                      # Migration environment config
│   └── versions/                   # Migration files
├── src/
│   ├── main.py                     # FastAPI app entry point
│   ├── core/
│   │   ├── config.py               # Settings (Pydantic Settings + .env)
│   │   └── security.py             # Password hashing & JWT utilities
│   ├── domain/                     # Business logic layer
│   │   ├── entities/               # Pure Python domain objects
│   │   ├── interfaces/             # Repository abstractions (ABCs)
│   │   └── services/               # Auth & task business logic
│   ├── infrastructure/
│   │   ├── database/               # SQLAlchemy models, repositories, connection
│   │   └── logging/                # structlog setup & request middleware
│   ├── api/
│   │   ├── dependencies.py         # FastAPI dependencies (auth, DB session)
│   │   └── routes/                 # auth.py, tasks.py
│   └── schemas/                    # Pydantic request/response schemas
├── tests/
│   ├── unit/                       # Service & repository unit tests (mock repos)
│   └── api/                        # Integration tests via FastAPI TestClient
├── docs/                           # Implementation & migration guides
├── alembic.ini
└── pyproject.toml
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL 17 (`brew install postgresql@17`)

### 1. Clone & install dependencies

```bash
cd fast_api_big_exercise
uv sync
```

### 2. Start PostgreSQL and create the database

```bash
brew services start postgresql@17

# Create the database (first time only)
export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"
psql postgres -c "CREATE ROLE taskmanager WITH LOGIN PASSWORD 'taskmanager_dev';"
psql postgres -c "CREATE DATABASE taskmanager_dev OWNER taskmanager;"
psql taskmanager_dev -c "GRANT ALL ON SCHEMA public TO taskmanager;"
```

### 3. Configure environment

```bash
cp .env.example .env
# .env is pre-configured for local PostgreSQL — edit if needed
```

### 4. Run database migrations

```bash
uv run alembic upgrade head
```

### 5. Start the API server

```bash
uv run uvicorn src.main:app --reload --port 8000
```

The API is now running at **http://localhost:8000**

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

---

## ⚙️ Configuration

All settings are loaded from a `.env` file via Pydantic Settings.

| Variable | Default | Description |
|---|---|---|
| `ENV` | `development` | Environment (`development` / `staging` / `production`) |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `postgresql://taskmanager:taskmanager_dev@localhost/taskmanager_dev` | DB connection string |
| `SECRET_KEY` | — | JWT secret (min 32 chars — **change in production!**) |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiry |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `console` | `console` (dev) or `json` (prod) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Allowed origins (comma-separated) |
| `DEFAULT_PAGE_SIZE` | `20` | Default pagination page size |

Generate a secure `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register a new user |
| `POST` | `/api/v1/auth/login` | Login and receive JWT token |

**Register:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com", "password": "secret123"}'
```

**Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=alice&password=secret123"
```

### Tasks (requires Bearer token)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/tasks` | List tasks (with filtering & pagination) |
| `POST` | `/api/v1/tasks` | Create a new task |
| `GET` | `/api/v1/tasks/{id}` | Get task by ID |
| `PATCH` | `/api/v1/tasks/{id}` | Update a task |
| `DELETE` | `/api/v1/tasks/{id}` | Delete a task |
| `GET` | `/api/v1/tasks/stats` | Task statistics |

**Create a task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Write tests", "priority": "high", "status": "todo"}'
```

**List tasks with filters:**
```bash
curl "http://localhost:8000/api/v1/tasks?status=todo&priority=high&limit=10" \
  -H "Authorization: Bearer <token>"
```

**Task fields:**

| Field | Values |
|-------|--------|
| `status` | `todo` / `in_progress` / `done` |
| `priority` | `low` / `medium` / `high` |
| `due_date` | ISO 8601 datetime (optional) |

---

## 🗃️ Database Migrations (Alembic)

Migrations run automatically on startup via `run_migrations()` in the app lifespan.

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Check if models are in sync with migrations
uv run alembic check

# View migration history
uv run alembic history --verbose

# Generate a new migration after changing models
uv run alembic revision --autogenerate -m "add column foo to tasks"

# Roll back one migration
uv run alembic downgrade -1

# Roll back all migrations
uv run alembic downgrade base
```

See [`docs/migration-guide.md`](docs/migration-guide.md) for the full setup walkthrough.

---

## 🧪 Testing

Tests use an **in-memory SQLite** database — no PostgreSQL required to run tests.

```bash
# Run all tests with coverage
uv run pytest --tb=short -q

# Run only unit tests
uv run pytest tests/unit/ -v

# Run only API integration tests
uv run pytest tests/api/ -v

# View HTML coverage report
open htmlcov/index.html
```

---

## 🏗️ Architecture

The project follows **clean architecture** with 4 distinct layers:

```
┌──────────────────────────────────────────────┐
│  API Layer  (src/api/)                       │  ← HTTP routes, request parsing
│  FastAPI routes, Pydantic schemas            │
├──────────────────────────────────────────────┤
│  Domain Layer  (src/domain/)                 │  ← Business logic
│  Entities, Repository interfaces, Services   │
├──────────────────────────────────────────────┤
│  Infrastructure Layer  (src/infrastructure/) │  ← External systems
│  SQLAlchemy repositories, structlog          │
├──────────────────────────────────────────────┤
│  Core Layer  (src/core/)                     │  ← Cross-cutting concerns
│  Config (settings), Security (JWT/bcrypt)    │
└──────────────────────────────────────────────┘
```

**Dependency direction:** API → Domain ← Infrastructure (domain has no external dependencies)

---

## 📦 Tech Stack

| Component | Library |
|-----------|---------|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Database ORM | [SQLAlchemy 2.0](https://docs.sqlalchemy.org/) |
| Database | [PostgreSQL 17](https://www.postgresql.org/) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Authentication | [PyJWT](https://pyjwt.readthedocs.io/) + [passlib](https://passlib.readthedocs.io/) |
| Settings | [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Logging | [structlog](https://www.structlog.org/) |
| Testing | [pytest](https://pytest.org/) + [httpx](https://www.python-httpx.org/) |
| Linting | [Ruff](https://docs.astral.sh/ruff/) |
| Package manager | [uv](https://docs.astral.sh/uv/) |

---

## 🔧 Development

```bash
# Lint
uv run ruff check src/

# Auto-fix lint issues (run from project root, then save)
uv run ruff check --fix src/

# Format
uv run ruff format src/

# Type check
uv run mypy src/
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [`docs/implementation-guide.md`](docs/implementation-guide.md) | Step-by-step build guide |
| [`docs/migration-guide.md`](docs/migration-guide.md) | Alembic setup & usage |
| [`docs/requirements.md`](docs/requirements.md) | Full feature specifications |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | Current project status |
