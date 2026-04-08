# Collaborative Project & Task Management API — Technical Guide

> A comprehensive guide for junior FastAPI developers to understand **why** each technology and capability was chosen, **what problem** it solves, and **how** it fits into the application.

---

## Table of Contents

1. [Tech Stack Explained](#1-tech-stack-explained)
2. [Key Capabilities Explained](#2-key-capabilities-explained)
3. [ERD (Entity Relationship Diagram) Explained](#3-erd-explained)
4. [Presentation Script](#4-presentation-script)

---

## 1. Tech Stack Explained

### 1.1 FastAPI + Uvicorn

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Traditional Python web frameworks (Flask, Django) run synchronously — each request blocks a thread until it finishes. For an API that handles many concurrent users, database queries, and WebSocket connections, this becomes a bottleneck. |
| **Why we chose it** | FastAPI is the fastest-growing Python web framework. It provides: **automatic OpenAPI docs** (Swagger UI), **built-in request validation** via Pydantic, **native async support**, and **dependency injection**. Uvicorn is a lightning-fast ASGI server that powers FastAPI's async capabilities. |
| **How it integrates** | `src/main.py` contains the **app factory** — a function that creates the FastAPI application, registers routers from `src/api/v1/`, adds middleware, and configures the lifespan (startup/shutdown events). Uvicorn runs this app in production. |

### 1.2 Pydantic v2

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Raw HTTP request data is unstructured (JSON strings, query params). Without validation, bad data reaches your database and causes crashes or security issues. Manually writing `if` checks for every field is tedious and error-prone. |
| **Why we chose it** | Pydantic v2 is a **data validation library** that uses Python type hints. It automatically validates, serializes, and documents request/response data. v2 is up to 50x faster than v1 because the core is written in Rust. FastAPI is built on top of Pydantic. |
| **How it integrates** | `src/schemas/` contains Pydantic models for each resource: `user.py`, `project.py`, `task.py`, `comment.py`, `common.py`. These schemas are used as **type hints** on route function parameters — FastAPI automatically validates incoming data and generates API docs from them. |

```python
# Example: src/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr          # Pydantic validates this is a real email
    password: str            # Must be a string
    full_name: str | None = None  # Optional field

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
```

### 1.3 SQLAlchemy 2.0 (Async)

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Writing raw SQL is error-prone, hard to maintain, and vulnerable to SQL injection. You also need to manually map database rows to Python objects. |
| **Why we chose it** | SQLAlchemy is the most mature Python ORM. Version 2.0 introduces a **modern, type-safe API** and **native async support** via `AsyncSession`. This means database queries don't block the event loop — other requests can be served while waiting for DB responses. |
| **How it integrates** | `src/infrastructure/database/models.py` defines **ORM models** (Python classes that map to database tables). `src/infrastructure/database/connection.py` sets up the **async engine** and **session factory**. `src/infrastructure/database/repositories.py` contains concrete repository implementations that use `AsyncSession` to query the database. |

```python
# Example: src/infrastructure/database/models.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="member")
```

### 1.4 PostgreSQL 17

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | SQLite (the default for small projects) doesn't support concurrent writes, has limited data types, and lacks advanced features like full-text search, JSONB, and row-level locking. For a production multi-user app, you need a real database. |
| **Why we chose it** | PostgreSQL is the most advanced open-source relational database. It supports **ACID transactions**, **advanced indexing**, **complex queries**, **enums**, and scales well for production workloads. It's the industry standard for Python web apps. |
| **How it integrates** | The connection URL is stored in `.env` and loaded by `src/core/config.py`. SQLAlchemy connects to PostgreSQL using the `asyncpg` driver (async PostgreSQL driver for Python). |

### 1.5 Alembic

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | As your app evolves, the database schema changes (new tables, new columns, renamed fields). Without a migration tool, you'd have to manually write SQL `ALTER TABLE` statements and run them on every environment (dev, staging, production). This is dangerous and error-prone. |
| **Why we chose it** | Alembic is the official migration tool for SQLAlchemy. It **auto-detects** changes in your ORM models and generates migration scripts. You can **upgrade** (apply changes) and **downgrade** (revert changes) your database schema safely. |
| **How it integrates** | The `alembic/` directory contains `env.py` (configuration), `script.py.mako` (template), and `versions/` (migration scripts). Running `alembic revision --autogenerate -m "add users table"` compares your models to the database and generates the migration. `alembic upgrade head` applies all pending migrations. |

### 1.6 PyJWT + passlib[bcrypt]

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | **Authentication**: How does the server know who is making a request? **Password security**: Storing passwords in plain text means a database breach exposes all user credentials. |
| **Why we chose it** | **PyJWT** creates and verifies JSON Web Tokens — stateless tokens that encode user identity. The server doesn't need to store session data. **passlib[bcrypt]** hashes passwords using the bcrypt algorithm, which is computationally expensive to brute-force. |
| **How it integrates** | `src/core/security.py` contains: `hash_password()` (bcrypt), `verify_password()` (bcrypt), `create_access_token()` (JWT), `create_refresh_token()` (JWT), `decode_token()` (JWT). Auth routes (`src/api/v1/auth.py`) use these utilities. The `get_current_user` dependency (`src/api/dependencies.py`) extracts and validates the JWT from each request's `Authorization` header. |

```
Client                         Server
  |                               |
  |-- POST /auth/login ---------->|
  |   (email + password)          |
  |                               |-- verify_password(password, hash)
  |                               |-- create_access_token(user_id)
  |<-- { access_token, refresh }--|
  |                               |
  |-- GET /users/me ------------->|
  |   Authorization: Bearer <jwt> |
  |                               |-- decode_token(jwt) → user_id
  |                               |-- get_user(user_id)
  |<-- { id, email, name } ------|
```

### 1.7 pytest + pytest-asyncio + httpx

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Without tests, you discover bugs in production. Every code change risks breaking existing features (regression). Manual testing is slow and unreliable. |
| **Why we chose it** | **pytest** is the most popular Python testing framework — simple syntax, powerful fixtures, plugins. **pytest-asyncio** lets you test `async` functions. **httpx** provides an `AsyncClient` that can send HTTP requests to your FastAPI app **without starting a real server** (in-process testing). |
| **How it integrates** | `tests/conftest.py` sets up fixtures: a **test database** (separate from production), an **async client**, and **auth helpers** (functions to quickly create users and get tokens). Each test file (`test_auth.py`, `test_users.py`, etc.) tests a specific feature area. |

```python
# Example: tests/test_auth.py
async def test_register(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepassword",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

### 1.8 Ruff + ty

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Inconsistent code style, unused imports, potential bugs, and type errors slow down code reviews and introduce bugs. |
| **Why we chose it** | **Ruff** is an extremely fast Python linter/formatter (written in Rust). It replaces `flake8`, `isort`, `black`, and `pyflakes` in a single tool. **ty** provides type checking to catch type mismatches before runtime. |
| **How it integrates** | Configured in `pyproject.toml`. Run `ruff check .` to lint and `ruff format .` to format. Run `ty` to type-check. These are run in CI/CD pipelines to enforce code quality. |

### 1.9 pydantic-settings + python-dotenv

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Hardcoding database URLs, secret keys, and API keys in source code is a **security risk** (they end up in Git history) and makes it impossible to have different configs for dev/staging/production. |
| **Why we chose it** | **pydantic-settings** loads configuration from environment variables with **type validation**. **python-dotenv** reads `.env` files so developers don't have to `export` variables manually. |
| **How it integrates** | `src/core/config.py` defines a `Settings` class. `.env.example` documents all required variables. At startup, `Settings()` reads from `.env` and validates all values. |

```python
# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    class Config:
        env_file = ".env"
```

### 1.10 structlog

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Python's built-in `logging` outputs plain text. In production, you need **structured (JSON) logs** that can be parsed by log aggregation tools (ELK Stack, Datadog, AWS CloudWatch). You also need **request tracing** — the ability to follow a single request through multiple log entries. |
| **Why we chose it** | **structlog** outputs logs as JSON with key-value pairs. It's easy to add context (request ID, user ID, execution time) that flows through all log entries for a single request. |
| **How it integrates** | `src/infrastructure/logging/setup.py` configures structlog. `src/infrastructure/logging/middleware.py` adds a **Request ID middleware** (generates a unique ID for each request) and a **timing middleware** (measures how long each request takes). These are added to the FastAPI app in `src/main.py`. |

```json
// Example log output
{
  "event": "request_completed",
  "request_id": "abc-123-def",
  "method": "GET",
  "path": "/api/v1/users/me",
  "status_code": 200,
  "duration_ms": 45.2,
  "timestamp": "2026-04-06T10:30:00Z"
}
```

---

## 2. Key Capabilities Explained

### 2.1 Multi-user Accounts

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | The app needs to identify **who** is performing actions. Different users have different data, different permissions, and different projects. |
| **Why we need it** | Without user accounts, everyone sees everything and anyone can modify anything. User accounts are the foundation of authentication and authorization. |
| **How it integrates** | `POST /auth/register` creates a user (hashed password stored in DB). `POST /auth/login` returns JWT tokens. `GET /users/me` returns the current user's profile. `PATCH /users/me` allows updating profile info. |

### 2.2 Project Management (CRUD + Membership)

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Users need to organize work into **projects** and control **who has access** to each project. A project owner should be able to invite members and assign roles. |
| **Why we need it** | This is the core organizational unit of the app. Without projects, tasks and comments have no context or access boundaries. |
| **How it integrates** | Projects have an **owner** (`owner_id → users.id`). Members are tracked via the **`project_members`** join table (N-N relationship with a `role` column). CRUD routes in `src/api/v1/projects.py` handle creation, listing, updating, deletion, and membership management. |

### 2.3 Task Tracking

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Teams need to track units of work: what needs to be done, who is responsible, what's the priority, and what's the current status. |
| **Why we need it** | Tasks are the primary work items. Without status transitions (`todo → in_progress → done`), filtering, sorting, and assignment, the app would be useless for project management. |
| **How it integrates** | Tasks belong to a **project** (`project_id`) and optionally to an **assignee** (`assignee_id`). They have `status` (enum: todo/in_progress/done) and `priority` (enum: low/medium/high). Routes support filtering by status/priority/assignee, sorting by created_at/due_date/priority, and pagination. |

### 2.4 Commenting

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Team members need to discuss tasks — ask questions, provide updates, share context. Without comments, all communication happens outside the app. |
| **Why we need it** | Comments provide an audit trail of discussions on each task. They're simple but essential for collaboration. |
| **How it integrates** | Comments belong to a **task** (`task_id`) and an **author** (`author_id`). Two endpoints: `POST /tasks/{task_id}/comments` (create) and `GET /tasks/{task_id}/comments` (list, paginated). |

### 2.5 Role-Based Access Control (RBAC)

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Not everyone should be able to do everything. An intern shouldn't be able to delete the entire project. A member shouldn't be able to remove other members. |
| **Why we need it** | RBAC provides **security boundaries**. It ensures users can only perform actions appropriate to their role, preventing accidental or malicious data modification. |
| **How it integrates** | Two layers of roles: **System role** (`UserRole`: admin/manager/member) and **Project role** (`ProjectMemberRole`: manager/member). `src/core/permissions.py` contains the permission checker. `src/api/dependencies.py` provides permission dependencies that are injected into routes. |

```
Admin           → Can do everything (system-wide)
Project Manager → Can manage members & tasks in own projects
Member          → Can create tasks, update own tasks, comment
```

### 2.6 JWT Auth + Refresh Tokens

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | **Sessions** require server-side storage (database/Redis) and don't scale well across multiple servers. Short-lived tokens expire quickly, forcing users to log in frequently. |
| **Why we need it** | **Access tokens** (short-lived, ~30 min) carry user identity statelessly. **Refresh tokens** (long-lived, ~7 days) allow getting new access tokens without re-entering credentials. This is the OAuth2 standard. |
| **How it integrates** | Login returns both tokens. The access token is sent in the `Authorization: Bearer <token>` header. When it expires, the client sends the refresh token to `POST /auth/refresh` to get a new pair. The `get_current_user` dependency validates the access token on every protected request. |

### 2.7 Async Everywhere

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Traditional sync code **blocks** while waiting for I/O (database queries, external API calls). A server with 10 threads can only handle 10 concurrent requests if each waits 1 second for the database. |
| **Why we need it** | With async, while one request waits for the database, the event loop handles other requests. This dramatically improves **throughput** — the same server can handle hundreds of concurrent connections. |
| **How it integrates** | All route handlers use `async def`. Database sessions use `AsyncSession`. The SQLAlchemy engine uses `create_async_engine()`. This means every database query is non-blocking. |

```python
# Sync (blocks the thread):
def get_user(db, user_id):
    return db.query(User).filter(User.id == user_id).first()

# Async (non-blocking):
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### 2.8 Background Tasks

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Some operations (sending emails, generating reports) are slow. If done inside the request handler, the user waits several seconds for a response. |
| **Why we need it** | Background tasks let you return a response **immediately** and perform slow work **after** the response is sent. The user doesn't wait. |
| **How it integrates** | FastAPI's `BackgroundTasks` is injected into route handlers. When a task is assigned or a project is created, a background task is added that simulates sending an email (logs a message). `src/infrastructure/background.py` contains the email simulation functions. |

```python
@router.post("/projects/{project_id}/tasks")
async def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    ...
):
    new_task = await task_service.create(task)
    background_tasks.add_task(send_assignment_email, new_task.assignee_id)
    return new_task  # Response sent immediately, email sent later
```

### 2.9 WebSocket Notifications

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | HTTP is **request-response** — the client must ask the server for updates. Without WebSockets, the client would need to **poll** (repeatedly ask "any updates?"), which wastes bandwidth and adds latency. |
| **Why we need it** | Real-time notifications let the server **push** updates to connected clients instantly. When a task status changes, all relevant users see it immediately. |
| **How it integrates** | `src/websockets/notifications.py` contains a **ConnectionManager** that tracks connected WebSocket clients. When a task status changes (in the task service), the manager broadcasts a notification to all connected users for that project. Clients connect via `ws://host/ws/notifications?token={jwt}`. |

### 2.10 Structured Logging

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Plain text logs (`print("User logged in")`) are impossible to search, filter, or aggregate at scale. In production with thousands of requests/second, you need to find the one request that failed. |
| **Why we need it** | JSON logs with **request IDs** let you trace a single request across all its log entries. **Execution timing** helps identify slow endpoints. Log aggregation tools (ELK, Datadog) can parse JSON automatically. |
| **How it integrates** | Middleware in `src/infrastructure/logging/middleware.py` generates a unique `request_id` for each request and measures execution time. structlog is configured in `src/infrastructure/logging/setup.py`. All log entries automatically include the request context. |

### 2.11 Testing ≥ 80% Coverage

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | Without tests, every deployment is a gamble. "It works on my machine" doesn't guarantee it works in production. Bugs in auth logic, permission checks, or data validation can go unnoticed. |
| **Why we need it** | 80% coverage ensures the **critical paths** are tested: auth flows, CRUD operations, permission denials, error handling. Tests serve as **living documentation** — they show how the API is meant to be used. |
| **How it integrates** | `tests/conftest.py` creates a separate test database and provides fixtures. Each test file covers a feature area. Run `pytest --cov` to measure coverage. Tests use `httpx.AsyncClient` to make real HTTP requests to the app in-process. |

### 2.12 Deployment Readiness

| Aspect | Detail |
|---|---|
| **What problem does it solve?** | A development-only app has hardcoded secrets, no health checks, and no configuration management. Deploying it to production requires manual work and is error-prone. |
| **Why we need it** | `.env.example` documents required environment variables. The `/health` endpoint lets load balancers check if the app is alive. Proper configuration separation (dev/staging/prod) prevents accidental use of test databases in production. |
| **How it integrates** | `GET /health` returns `{"status": "healthy"}`. `.env.example` lists all required variables with placeholder values. `src/core/config.py` validates all configuration at startup — the app **fails fast** if a required variable is missing. |

---

## 3. ERD Explained

### What is an ERD?

An **Entity Relationship Diagram** visualizes the database structure: which tables exist, what columns they have, and how they relate to each other.

### The 5 Tables

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│    users      │     │ project_members   │     │   projects    │
├──────────────┤     ├──────────────────┤     ├──────────────┤
│ id (PK)      │◄──┐ │ id (PK)          │ ┌──►│ id (PK)      │
│ email        │   ├─│ user_id (FK)     │ │   │ name         │
│ hashed_pass  │   │ │ project_id (FK)──│─┘   │ description  │
│ full_name    │   │ │ role             │     │ owner_id (FK)│──┐
│ role         │   │ └──────────────────┘     │ created_at   │  │
│ created_at   │   │                          │ updated_at   │  │
│ updated_at   │   │                          └──────────────┘  │
└──────────────┘   │                                            │
       ▲           │   ┌──────────────┐                        │
       │           │   │    tasks      │                        │
       │           │   ├──────────────┤                        │
       │           ├──►│ id (PK)      │                        │
       │           │   │ title        │                        │
       │           │   │ description  │                        │
       │           │   │ status       │  (todo/in_progress/done)
       │           │   │ priority     │  (low/medium/high)
       │           │   │ project_id(FK)│──────────────────────┘
       │           ├───│ creator_id(FK)│
       │           │   │ assignee_id(FK)│ (nullable)
       │           │   │ due_date     │
       │           │   │ created_at   │
       │           │   │ updated_at   │
       │           │   └──────────────┘
       │           │          │
       │           │          │ 1-N
       │           │          ▼
       │           │   ┌──────────────┐
       │           │   │   comments    │
       │           │   ├──────────────┤
       │           │   │ id (PK)      │
       │           └───│ author_id(FK)│
       │               │ task_id (FK) │
       └───────────────│ content      │
                       │ created_at   │
                       │ updated_at   │
                       └──────────────┘
```

### Relationships Explained

| Relationship | Type | Why? |
|---|---|---|
| **User → Projects (owner)** | 1-N | One user can own many projects, but each project has exactly one owner. The `owner_id` column in the `projects` table is a foreign key to `users.id`. |
| **User ↔ Projects (member)** | N-N | A user can be a member of many projects. A project can have many members. This N-N relationship requires a **join table** (`project_members`) that also stores the member's `role` within that project. |
| **Project → Tasks** | 1-N | A project contains many tasks. Each task belongs to exactly one project. `tasks.project_id` references `projects.id`. |
| **User → Tasks (creator)** | 1-N | One user can create many tasks. Each task has exactly one creator. `tasks.creator_id` references `users.id`. This is **not nullable** — every task must have a creator. |
| **User → Tasks (assignee)** | 1-N | One user can be assigned many tasks. Each task has at most one assignee. `tasks.assignee_id` references `users.id`. This is **nullable** — tasks can be unassigned. |
| **User → Comments** | 1-N | One user can write many comments. Each comment has exactly one author. `comments.author_id` references `users.id`. |
| **Task → Comments** | 1-N | A task can have many comments. Each comment belongs to exactly one task. `comments.task_id` references `tasks.id`. |

### Enums Explained

Enums restrict a column to a predefined set of values, preventing invalid data:

| Enum | Values | Purpose |
|---|---|---|
| `UserRole` | admin, manager, member | **System-wide** role. Determines global permissions (e.g., only admin can delete projects). |
| `ProjectMemberRole` | manager, member | **Per-project** role. Determines what a user can do within a specific project. |
| `TaskStatus` | todo, in_progress, done | Tracks the lifecycle of a task. Status transitions are validated in business logic. |
| `TaskPriority` | low, medium, high | Allows filtering and sorting tasks by urgency. |

### Why the `project_members` Join Table?

The N-N relationship between Users and Projects can't be represented with a simple foreign key. Consider:

- User A is a member of Project 1 (as manager) AND Project 2 (as member)
- Project 1 has User A, User B, and User C as members

You need a separate row for each user-project combination:

| user_id | project_id | role    |
|---------|------------|---------|
| 1       | 1          | manager |
| 1       | 2          | member  |
| 2       | 1          | member  |
| 3       | 1          | member  |

This also allows storing the **role** each user has within each specific project.

---

## 4. Presentation Script

### Slide 1: Title & Introduction

> "Hello everyone. Today I'll walk you through the architecture and technology choices for our **Collaborative Project & Task Management API** — a backend system similar to Trello or Jira.
>
> I'll cover three things for each technology: **what problem** it solves, **why** we chose it over alternatives, and **how** it fits into our codebase. By the end, you'll understand not just *what* we're building, but *why* every piece exists."

---

### Slide 2: Project Overview

> "At its core, this is a **REST API** where users create projects, invite team members, create and assign tasks, leave comments, and receive real-time notifications.
>
> The key architectural principle is **clean separation of concerns**: domain logic knows nothing about FastAPI, database implementations are swappable, and the API layer is thin — it just validates input, calls services, and returns responses.
>
> Our project follows a structure with five main layers: **core** (config, security), **domain** (pure business logic with no framework imports), **infrastructure** (database, logging), **schemas** (Pydantic validation), and **api** (route handlers)."

---

### Slide 3: FastAPI + Uvicorn

> "We chose **FastAPI** as our framework for three key reasons.
>
> First, it's **async-native**. Traditional frameworks like Flask or Django handle one request per thread. FastAPI uses Python's asyncio, meaning while one request waits for a database query, the server handles other requests. This is critical for our WebSocket feature.
>
> Second, **automatic documentation**. FastAPI generates interactive Swagger UI docs from your code. When you add a Pydantic model as a parameter type hint, it appears in the docs automatically — no manual documentation needed.
>
> Third, **dependency injection**. Need database access? Define a dependency. Need the current user? Define a dependency. Need permission checks? Chain dependencies. This makes our code modular and testable.
>
> Uvicorn is the ASGI server that actually runs FastAPI. Think of FastAPI as the application and Uvicorn as the web server."

---

### Slide 4: Pydantic v2 — The Validation Layer

> "Every HTTP request contains untrusted data. A user could send an integer where we expect a string, an invalid email, or a negative number for a task priority.
>
> **Pydantic v2** solves this. We define schemas — Python classes with type hints — and FastAPI automatically validates every request against them. If validation fails, the user gets a clear error message with zero code from us.
>
> For example, our `UserCreate` schema ensures the email field is actually a valid email address. If someone sends `'not-an-email'`, Pydantic rejects it before our code even runs.
>
> V2 is up to 50x faster than v1 because the validation core is written in Rust. Our schemas live in `src/schemas/` — one file per resource."

---

### Slide 5: SQLAlchemy 2.0 (Async) + PostgreSQL

> "We need a database, and we need to talk to it from Python.
>
> **PostgreSQL** is our database because it supports concurrent users, ACID transactions, advanced indexing, and enum types — all things SQLite can't do. It's the industry standard for production Python apps.
>
> **SQLAlchemy 2.0** is our ORM — it maps Python classes to database tables. Instead of writing raw SQL like `SELECT * FROM users WHERE id = 5`, we write `select(User).where(User.id == 5)`. This prevents SQL injection and makes our code database-agnostic.
>
> The key word here is **async**. We use `AsyncSession` and `create_async_engine`, which means database queries don't block the event loop. While waiting for PostgreSQL to return results, our server handles other requests."

---

### Slide 6: Alembic — Database Migrations

> "Imagine your app is in production with 10,000 users. You need to add a `due_date` column to the tasks table. You can't just drop and recreate the database — you'd lose all the data.
>
> **Alembic** solves this. It's SQLAlchemy's migration tool. When you change an ORM model, Alembic auto-generates a migration script that describes the change. Running `alembic upgrade head` applies all pending migrations safely.
>
> The beauty is that migrations are **versioned** and **reversible**. If a migration causes problems, you can `alembic downgrade` to roll it back. Every migration is stored as a Python file in `alembic/versions/`, creating a complete history of your database schema evolution."

---

### Slide 7: Authentication — JWT + bcrypt

> "Authentication answers the question: **who are you?**
>
> We use the **OAuth2 Password flow**: the user sends email + password, and we return two tokens.
>
> The **access token** is a JWT — a signed JSON payload containing the user's ID. It's short-lived (30 minutes) so if it's stolen, the damage is limited. The client sends it in the `Authorization: Bearer <token>` header with every request.
>
> The **refresh token** is long-lived (7 days). When the access token expires, the client exchanges the refresh token for a new pair. This avoids asking the user to log in every 30 minutes.
>
> Passwords are **never stored in plain text**. We use **bcrypt** to hash them. Even if the database is breached, attackers can't reverse the hashes into passwords. The `get_current_user` dependency in every protected route extracts and validates the JWT automatically."

---

### Slide 8: RBAC — Role-Based Access Control

> "Authentication tells us **who** the user is. Authorization tells us **what** they can do. That's RBAC.
>
> We have two levels of roles. **System roles**: Admin can do everything system-wide. Manager and Member have limited global permissions.
>
> **Project roles**: Within each project, a user can be a Manager (can add/remove members, modify any task) or a Member (can only modify their own tasks).
>
> For example: when a Member tries to delete a task, we check: Are they the task creator? If not, deny. When a Project Manager tries to add a member, we check: Are they a manager of THIS project? If not, deny.
>
> Permissions are implemented as **FastAPI dependencies** in `src/core/permissions.py` and injected into routes. This keeps permission logic separate from business logic."

---

### Slide 9: ERD — Database Design

> "Let's look at our database design. We have **5 tables** connected by foreign keys.
>
> The **users** table is central — it connects to almost everything. A user can own projects, be a member of projects, create tasks, be assigned tasks, and write comments.
>
> The interesting design choice is the **project_members** table. Users and Projects have a many-to-many relationship — one user can be in many projects, one project can have many users. SQL doesn't support N-N directly, so we use a **join table** that stores which user is in which project AND their role within that project.
>
> Tasks have **two** foreign keys to users: `creator_id` (who created it, never null) and `assignee_id` (who's working on it, nullable — tasks can be unassigned).
>
> We use **enums** for constrained fields: TaskStatus can only be 'todo', 'in_progress', or 'done'. This prevents invalid data at the database level."

---

### Slide 10: Async Programming

> "This is perhaps the most important architectural decision. **Everything is async.**
>
> In synchronous code, when your handler queries the database, the entire thread is blocked waiting for the response. With 10 threads and 10 concurrent requests that each take 1 second to query the DB, your 11th user waits.
>
> In async code, when your handler `await`s a database query, the event loop pauses that coroutine and picks up another request. When the database responds, the original coroutine resumes. One thread can handle hundreds of concurrent requests.
>
> This is why we use `async def` for all routes, `AsyncSession` for database access, and `await` for every I/O operation. It's critical for our WebSocket feature — we need to handle many persistent connections simultaneously."

---

### Slide 11: Background Tasks + WebSockets

> "Two features that improve user experience:
>
> **Background Tasks**: When a task is assigned, we want to 'send an email.' But email sending takes 2-3 seconds. With `BackgroundTasks`, we return the response immediately and send the email after. The user doesn't wait. In our case, we simulate the email by logging a message, but the pattern is production-ready.
>
> **WebSockets**: Normal HTTP is request-response — the client asks, the server answers. But what if a teammate changes a task status? Without WebSockets, you'd have to refresh the page or poll the server every few seconds.
>
> WebSockets keep a persistent connection open. When a task status changes, the server pushes a notification to all connected project members instantly. Our `ConnectionManager` in `src/websockets/notifications.py` tracks connected clients and broadcasts events."

---

### Slide 12: Logging + Middleware

> "In production, you can't attach a debugger. You need **logs**.
>
> We use **structlog** which outputs JSON — not plain text. Why? Because log aggregation tools (ELK Stack, Datadog, CloudWatch) can parse JSON automatically. You can search for `{"request_id": "abc-123"}` and see every log entry for that specific request.
>
> Our middleware stack adds two things to every request:
> 1. A **unique request ID** — so you can trace a single request across all its log entries
> 2. **Execution timing** — so you can identify slow endpoints
>
> If a user reports a bug and gives you the request ID, you can find exactly what happened in the logs."

---

### Slide 13: Testing Strategy

> "Our testing strategy uses **pytest** with **httpx** for async HTTP testing. The key insight is that httpx can call our FastAPI app directly — no real server needed.
>
> We have a **separate test database** (configured in `tests/conftest.py`). Before each test, we create fresh tables. After each test, we roll back all changes. Tests are isolated — they can run in any order.
>
> We test five things:
> 1. **Happy paths** — registration, login, CRUD operations
> 2. **Validation errors** — invalid emails, missing fields
> 3. **Permission denials** — member tries to delete a project
> 4. **Edge cases** — duplicate emails, expired tokens
> 5. **Full lifecycles** — create project → add member → create task → assign → comment → change status
>
> Our target is **80% code coverage**, which ensures all critical paths are tested."

---

### Slide 14: Clean Architecture

> "Our project structure follows **clean architecture** principles. The key rule: **dependencies point inward**.
>
> The **domain layer** (`src/domain/`) contains pure business logic — plain Python dataclasses and abstract repository interfaces. It has **zero framework imports**. You could theoretically replace FastAPI with Django and the domain layer wouldn't change.
>
> The **infrastructure layer** (`src/infrastructure/`) contains framework-specific implementations — SQLAlchemy models, concrete repository implementations, structlog configuration.
>
> The **API layer** (`src/api/`) is thin — it validates input, calls services, and returns responses.
>
> This separation makes the code **testable** (you can mock repositories), **maintainable** (changing the database doesn't affect business logic), and **understandable** (each file has one responsibility)."

---

### Slide 15: Deployment Readiness

> "Finally, we make the app **production-ready** with a few simple but critical features:
>
> A **health check endpoint** (`GET /health`) returns `{'status': 'healthy'}`. Load balancers use this to know if the app is alive. If the app crashes, the load balancer stops routing traffic to it.
>
> A **`.env.example`** file documents every required environment variable. A new developer can copy it to `.env`, fill in their values, and run the app immediately.
>
> **Configuration validation** — if a required variable is missing, the app **fails at startup** with a clear error, not in the middle of serving requests.
>
> These are small things that make the difference between a demo project and a production-ready system."

---

### Slide 16: Summary & Q&A

> "To summarize:
>
> - **FastAPI + Pydantic** give us automatic validation and documentation
> - **SQLAlchemy + PostgreSQL + Alembic** give us a robust, evolvable data layer
> - **JWT + bcrypt + RBAC** give us secure authentication and fine-grained authorization
> - **Async everywhere** gives us high throughput for concurrent users
> - **Background tasks + WebSockets** give us responsive UX and real-time updates
> - **structlog + middleware** give us production-grade observability
> - **pytest + 80% coverage** gives us confidence in every deployment
> - **Clean architecture** gives us maintainability as the codebase grows
>
> Every technology was chosen to solve a specific problem. There are no 'nice-to-haves' here — each piece is essential for a production-ready collaborative API.
>
> Any questions?"