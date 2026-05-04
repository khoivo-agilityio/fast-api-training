# AI-Enhanced Learning Platform API

Backend REST API for an AI-Enhanced Learning Platform built with FastAPI.

## Tech Stack

- **Runtime**: Python 3.11+, FastAPI, Uvicorn
- **Database**: PostgreSQL 16, SQLAlchemy 2.0 (async)
- **Auth**: PyJWT + bcrypt (access + refresh tokens)
- **Cache**: Redis (async) — token blacklist, session store
- **Migrations**: Alembic
- **Testing**: pytest + pytest-asyncio + httpx + aiosqlite
- **Admin UI**: SQLAdmin
- **Linting**: Ruff
- **Package Manager**: uv

## Setup

```bash
# Install dependencies
uv sync

# Copy environment config
cp .env.example .env
# Edit .env with your values

# Start PostgreSQL + Redis
docker compose up -d db redis

# Run migrations
uv run python -m alembic upgrade head

# Start development server
uv run python -m uvicorn src.main:app --reload --port 8001
```

## API Documentation

- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- Health check: http://localhost:8001/health

## Testing

```bash
# Run tests
uv run pytest tests/ --tb=short -q

# Run tests with coverage
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/
```

## Project Structure

```
src/
├── auth/           # Authentication & token management
├── users/          # User profile management
├── courses/        # Course management + enrollment
├── lessons/        # Lesson management + viewing
├── quizzes/        # Quiz & question management
├── submissions/    # Quiz taking & auto-grading
├── progress/       # Progress tracking
├── admin/          # Admin REST + SQLAdmin UI
├── config.py       # Settings (pydantic-settings)
├── database.py     # Async SQLAlchemy engine
├── redis.py        # Async Redis client
├── exceptions.py   # Domain error hierarchy
├── pagination.py   # Shared pagination utilities
├── models.py       # ORM model re-exports (for Alembic)
└── main.py         # App factory
```

## Docker

```bash
# Full stack
docker compose up -d --build

# Logs
docker compose logs app --tail=50

# Shut down
docker compose down
```
