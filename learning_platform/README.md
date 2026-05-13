# AI-Enhanced Learning Platform API

Backend REST API for an AI-Enhanced Learning Platform built with FastAPI.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Runtime | Python 3.11+, FastAPI, Uvicorn |
| Database | PostgreSQL 16, SQLAlchemy 2.0 (async) |
| Auth | PyJWT + bcrypt (access + refresh tokens) |
| Cache | Redis 7 (async) — token blacklist, session store |
| Migrations | Alembic |
| Testing | pytest + pytest-asyncio + httpx + aiosqlite |
| Admin UI | SQLAdmin (web panel at `/admin`) |
| Linting | Ruff |
| Package Manager | uv |

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for PostgreSQL, Redis, and MinIO)
- [uv](https://docs.astral.sh/uv/) — `brew install uv` or `pip install uv`
- Python 3.11+ (managed by uv automatically)

---

## Quick Start

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# The defaults in .env.example work out of the box with Docker
```

> **Important**: Never leave `.env` empty. Copy from `.env.example` first.

### 3. Start infrastructure via Docker

```bash
docker compose up -d db redis minio
```

Verify containers are healthy:

```bash
docker compose ps
# db, redis, and minio should all show status "healthy"
```

> **MinIO console** (S3-compatible local storage) is available at **http://localhost:9001**
> Login: `minioadmin` / `minioadmin`

### 4. Run database migrations

```bash
uv run python -m alembic upgrade head
```

### 5. Start the development server

There are **two ways** to run the server. Choose one:

#### Option A — Direct (recommended for day-to-day dev)

Runs uvicorn on your Mac. The `.env` file uses `localhost` for all service URLs.

```bash
uv run python -m uvicorn src.main:app --reload --port 8001
```

#### Option B — Full Docker stack

Runs everything inside Docker Compose. Service URLs are automatically overridden to Docker-internal hostnames (`db`, `redis`, `minio`).

```bash
docker compose up -d --build
```

> ⚠️ **Do not mix the two modes.** If you run uvicorn directly (Option A) but your `.env` has Docker-internal hostnames like `db` or `redis`, you will get `nodename nor servname provided` errors.

The API is now live at **http://localhost:8001**

---

## API Documentation

| Interface | URL |
|-----------|-----|
| Swagger UI (interactive) | http://localhost:8001/docs |
| ReDoc | http://localhost:8001/redoc |
| Health check | http://localhost:8001/health |
| **SQLAdmin Web UI** | **http://localhost:8001/admin** |

---

## Admin Web UI (SQLAdmin)

The SQLAdmin panel is available at **http://localhost:8001/admin** and provides a browser-based interface to view and manage all database records.

### Admin Login Credentials

The admin account must be created via the API first (see [Test Users](#test-users-for-manual-testing) below).

| Field | Value |
|-------|-------|
| Username | `admin@example.com` |
| Password | `Admin1234!` |

### What you can manage in SQLAdmin

- **Users** — view all users, roles, email
- **Courses** — browse all courses and instructors
- **Enrollments** — see who enrolled in what
- **Lessons** — view lesson content and ordering
- **Quizzes & Questions** — inspect quiz structure
- **Submissions & Answers** — see student attempts and scores
- **Progress Records** — track lesson completion per user

---

## Test Users for Manual Testing

> **⚠️ Role restriction:** The `POST /api/v1/auth/register` endpoint only allows registering accounts with the `student` role. To create `admin` or `instructor` accounts, use the **SQLAdmin panel** (`/admin`).

### Register a Student via API — `POST /api/v1/auth/register`

```json
{
  "email": "student@example.com",
  "password": "Student1234!",
  "display_name": "John Student"
}
```

> The `role` field defaults to `"student"` and cannot be overridden via the public API.

### Create Admin / Instructor via SQLAdmin

1. Open **`/admin`** and log in with a superuser account
2. Navigate to **Users → Create**
3. Set `role` to `admin` or `instructor` manually

Recommended test credentials:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@example.com` | `Admin1234!` |
| Instructor | `instructor@example.com` | `Instructor1234!` |
| Student | `student@example.com` | `Student1234!` |


---

## Connecting TablePlus (or any DB client)

The database runs in Docker and is exposed on **localhost:5432**.

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5432` |
| User | `postgres` |
| Password | `postgres` |
| Database | `learning_platform` |

> **Troubleshooting `Connection refused`**: This means the Docker containers are not running.
> Run `docker compose up -d db redis` to start them, then retry the connection.

---

## Testing

### Run the pytest suite (uses SQLite in-memory — no Docker needed)

```bash
# Quick run
uv run pytest tests/ --tb=short -q

# With coverage report
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

### Run Postman / Newman end-to-end tests (requires running server + Docker)

```bash
# Install Newman globally
npm install -g newman

# Run the full Postman collection
newman run docs/postman_collection_all.json \
  --environment docs/postman_environment_all.json \
  --bail

# Run only Phase 4 + 5 tests
newman run docs/postman_collection_phase45.json \
  --environment docs/postman_environment_phase45.json \
  --bail
```

The Postman collections automate the full E2E flow:
1. Register admin / instructor / student
2. Login and capture tokens
3. Create courses, lessons, quizzes
4. Enroll student, complete lessons, take quizzes
5. Admin CRUD operations

### Linting & Formatting

```bash
# Check for issues
uv run ruff check src/ tests/

# Auto-fix
uv run ruff check src/ tests/ --fix

# Format code
uv run ruff format src/ tests/
```

---

## Project Structure

```
learning_platform/
├── src/
│   ├── auth/           # Registration, login, JWT, refresh tokens
│   ├── users/          # User profile management
│   ├── courses/        # Course CRUD + enrollment
│   ├── lessons/        # Lesson management + viewing
│   ├── quizzes/        # Quiz & question management
│   ├── submissions/    # Quiz taking & auto-grading
│   ├── progress/       # Lesson progress tracking
│   ├── admin/          # Admin REST API + SQLAdmin UI
│   ├── config.py       # Settings (pydantic-settings)
│   ├── database.py     # Async SQLAlchemy engine
│   ├── redis.py        # Async Redis client
│   ├── exceptions.py   # Domain error hierarchy
│   ├── pagination.py   # Shared pagination utilities
│   ├── models.py       # ORM model re-exports (for Alembic)
│   └── main.py         # App factory
├── tests/              # pytest test suite (SQLite)
├── alembic/            # Database migrations
├── docs/               # Postman collections + API specs
├── docker-compose.yml  # PostgreSQL + Redis services
├── Dockerfile          # Production container
├── pyproject.toml      # Project config + dependencies
├── .env.example        # Environment template
└── gotchas.md          # Known issues and solutions
```

---

## Docker

```bash
# Start only infrastructure (db + redis + minio) — for Option A dev workflow
docker compose up -d db redis minio

# Full stack (app + db + redis + minio) — Option B, mirrors production
docker compose up -d --build

# View app logs
docker compose logs app --tail=50

# Follow logs live
docker compose logs -f

# Stop everything (preserves volumes)
docker compose down

# Stop and wipe all data including MinIO objects
docker compose down -v
```

---

## Common Issues

| Symptom | Fix |
|---------|-----|
| `Connection refused` on port 5432 | Run `docker compose up -d db redis minio` |
| `Connection refused` on port 6379 | Same — Redis not started |
| `Connection refused` on port 9000 | MinIO not started — run `docker compose up -d minio` |
| `nodename nor servname provided` (`db` or `redis`) | You have Docker-internal hostnames in `.env` but are running uvicorn directly. Use `localhost` in `.env` for Option A. |
| `ECONNREFUSED 127.0.0.1:9000` (from client upload) | `S3_ENDPOINT_URL` in `.env` should be `http://localhost:9000` for Option A; Docker Compose overrides it automatically for Option B. |
| TablePlus can't connect | Docker containers must be running first |
| `alembic upgrade head` fails | Start Docker first (`docker compose up -d db`), then run migrations |
| SQLAdmin login rejected | Register the admin user via API first |
| Empty `.env` file | Copy from `.env.example`: `cp .env.example .env` |

