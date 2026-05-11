# AI-Enhanced Learning Platform — Analysis & Implementation Plan

**Target AI Agent**: Claude Sonnet 4.6  
**Date**: April 22, 2026  
**Author**: KhoiVo

---

## 0. Meta — About This Prompt

### Original Prompt Summary
> "Follow previous analysys_plan.md. Continue analysis the [KhoiVo] FastAPI - Big Practice.md. Require: note this prompt in the plan, define execution and verification steps, write detailed specs for Claude Sonnet 4.6, log mistakes in gotchas.md, update .claude/CLAUDE.md and .github/copilot-instructions.md, indicate all changes (DTOs, decorators, controller, services, tests), create API changelog after implementation, ask if unclear."

### Clarifications Resolved (Before Writing This Plan)
| # | Question | Decision |
|---|----------|----------|
| Q1 | AI features? | **Bypass** — "AI-Enhanced" is branding only; no AI features in this iteration |
| Q2 | Architecture layer: domain-driven vs repositories? | **Use repositories layer** (routers → services → repositories → schemas); update Copilot instructions accordingly |
| Q3 | WebSocket notifications? | **Bypass** — not needed |
| Q4 | Refresh tokens? | **Yes** — access + refresh token rotation |
| Q5 | SQLAdmin? | **Yes** — include as required feature |
| Q6 | Redis? | **Yes** — needed (caching, session store for tokens) |
| Q7 | Quiz question type? | **Single/multiple choice only** + auto-grading for multiple choice |
| Q8 | Progress tracking? | **Course level only**. Lesson completed by: passing its quiz (if quiz exists), or simply visiting (if no quiz) |

### Pros & Cons of This Prompt

**Pros:**
- Good context reference (links to prior plan and practice doc)
- Clear deliverable list (DTOs, services, tests, changelog)
- Specifies target agent model
- Asks about error tracking and instruction updates

**Cons / Improvements:**
- "Follow previous analysys_plan.md" assumes the agent can locate the file — should include an explicit path or paste key sections
- "Continue analysis" is vague; a better prompt would say "produce a new standalone plan for learning_platform, using fast_api_practice/docs/analysys_plan.md as a style reference"
- Does not specify test coverage target (e.g. ≥ 80%)
- "Decorators" is a DRF/Django term; should be "dependencies / middleware / route guards" for FastAPI
- No mention of Alembic migration strategy

**Improved Prompt Template:**
```
Using fast_api_practice/docs/analysys_plan.md as a style reference, produce a
complete implementation plan for learning_platform/ (see docs/[KhoiVo] FastAPI -
Big Practice.md). The plan must:
- Follow the repositories layer: routers → services → repositories → schemas
- Cover DTOs (Pydantic schemas), ORM models, route handlers, services,
  repositories, tests (≥ 80% coverage)
- Define execution steps (commands to run) and verification steps (lint + test)
- Include Alembic migration strategy
- Specify that mistakes must be logged in gotchas.md and propagated to
  .claude/CLAUDE.md and .github/copilot-instructions.md
- Require an API changelog in docs/api/ after implementation
Target model: Claude Sonnet 4.6
```

---

## 1. Project Overview

**What**: Backend REST API for an AI-Enhanced Learning Platform (no AI features in v1).

**Roles**: Admin | Instructor | Student

**Key capabilities** (all mandatory):

| # | Capability | Notes |
|---|---|---|
| 1 | Multi-user accounts | Register, login, profile, role-based access |
| 2 | JWT auth + refresh tokens | OAuth2 Password flow, bcrypt |
| 3 | Course management | CRUD by instructor; enrollment by student |
| 4 | Lesson management | Text-only content; belongs to course |
| 5 | Quiz management | Single/multiple choice; linked to lesson |
| 6 | Quiz auto-grading | Multiple-choice questions auto-scored |
| 7 | Submission handling | Student submits answers; score computed |
| 8 | Course progress tracking | Course-level; driven by lesson completion |
| 9 | Admin CRUD APIs + SQLAdmin UI | Manage users, courses, lessons, assessments, records |
| 10 | RBAC | Admin / Instructor / Student |
| 11 | Testing ≥ 80% coverage | pytest + aiosqlite (never real PostgreSQL in tests) |
| 12 | Docker + Railway deployment | Multi-stage Dockerfile, Railway-ready |
| 13 | Redis | Caching; token blacklist for logout |

**Tech Stack** (mandatory):

| Layer | Choice |
|---|---|
| Runtime | Python 3.11+, FastAPI, Uvicorn |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Auth | PyJWT + passlib[bcrypt] |
| Cache / Token store | Redis (aioredis / redis-py async) |
| Testing | pytest + pytest-asyncio + httpx + aiosqlite |
| Linting | Ruff |
| Config | pydantic-settings + python-dotenv |
| Admin UI | SQLAdmin |
| Package manager | uv (pyproject.toml + uv.lock) |
| Containerisation | Docker multi-stage, Docker Compose |
| Deployment | Railway (Dockerfile builder) |

---

## 2. Architecture

### Module-Based Project Structure

This project follows the **module-by-feature** layout recommended in
[zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices#project-structure).
Each business domain (auth, courses, lessons, quizzes, submissions, progress,
users, admin) is a **self-contained Python package** under `src/` that owns its
router, schemas, models, service, dependencies, exceptions, constants and
utilities. Cross-cutting concerns (config, database, top-level exceptions,
shared models) live at the top of `src/`.

```text
learning_platform/
├── alembic/
├── src/
│   ├── auth/                    # F1 — Authentication & Token Management
│   │   ├── __init__.py
│   │   ├── router.py            # POST /auth/{register,login,refresh,logout}
│   │   ├── schemas.py           # Register/Login/Token/Refresh DTOs
│   │   ├── models.py            # (auth-specific tables, e.g. refresh tokens)
│   │   ├── dependencies.py      # get_current_user, require_roles
│   │   ├── service.py           # AuthService — business logic
│   │   ├── exceptions.py        # InvalidCredentials, TokenRevoked, ...
│   │   ├── constants.py         # JWT alg, token TTLs, error codes
│   │   ├── jwt.py               # encode/decode access + refresh tokens
│   │   ├── security.py          # bcrypt hash/verify
│   │   └── utils.py
│   ├── users/                   # F2 — User Profile Management
│   │   ├── router.py            # /users/me
│   │   ├── schemas.py
│   │   ├── models.py            # User ORM
│   │   ├── service.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   ├── courses/                 # F3 + F4 — Course Mgmt + Discovery + Enrollment
│   │   ├── router.py            # /courses/...
│   │   ├── schemas.py
│   │   ├── models.py            # Course, Enrollment ORM
│   │   ├── service.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   ├── lessons/                 # F5 + F6 — Lesson Mgmt + Viewing/Completion
│   │   ├── router.py            # /courses/{cid}/lessons, /lessons/{id}
│   │   ├── schemas.py
│   │   ├── models.py            # Lesson ORM
│   │   ├── service.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   ├── quizzes/                 # F7 — Quiz & Question Management
│   │   ├── router.py            # /lessons/{lid}/quiz, /quizzes/{qid}/questions
│   │   ├── schemas.py
│   │   ├── models.py            # Quiz, Question ORM (Question.options as JSON)
│   │   ├── service.py
│   │   ├── exceptions.py
│   │   └── dependencies.py
│   ├── submissions/             # F8 — Quiz Taking & Auto-grading
│   │   ├── router.py            # /quizzes/{qid}/{submit,submission}
│   │   ├── schemas.py
│   │   ├── models.py            # Submission, Answer ORM
│   │   ├── service.py           # SubmissionService.auto_grade(...)
│   │   ├── exceptions.py
│   │   └── grading.py           # pure grading helpers
│   ├── progress/                # F9 — Progress Tracking
│   │   ├── router.py            # /courses/{cid}/progress, /progress
│   │   ├── schemas.py
│   │   ├── models.py            # Progress ORM (status enum)
│   │   ├── service.py           # ProgressService.recalculate(...)
│   │   └── exceptions.py
│   ├── admin/                   # F10 — Admin REST + SQLAdmin UI
│   │   ├── router.py            # /api/v1/admin/*
│   │   ├── views.py             # SQLAdmin ModelViews
│   │   ├── auth.py              # SQLAdmin AuthenticationBackend
│   │   └── dependencies.py
│   ├── config.py                # Settings (pydantic-settings, env vars)
│   ├── database.py              # Async engine, session factory, Base, get_db
│   ├── redis.py                 # Async Redis client + blacklist helpers
│   ├── logging.py               # structlog setup
│   ├── exceptions.py            # DomainError base hierarchy
│   ├── pagination.py            # PaginationParams, PageResponse[T]
│   ├── models.py                # Re-exports all ORM models for Alembic autogen
│   └── main.py                  # App factory, mount routers, exception handlers
├── tests/
│   ├── auth/
│   ├── users/
│   ├── courses/
│   ├── lessons/
│   ├── quizzes/
│   ├── submissions/
│   ├── progress/
│   ├── admin/
│   └── conftest.py
├── docs/
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── pyproject.toml
└── README.md
```

### Why module-based (vs. layer-based)

| Aspect | Layer-based (`api/`, `services/`, `repositories/`) | Module-based (this plan) |
| --- | --- | --- |
| Onboarding | New devs must touch 4–5 folders to follow one feature | Open one folder → see everything for that feature |
| Coupling | Easy to leak business logic across layers | Each module is a clear bounded context |
| Refactoring | Renaming a feature touches every layer folder | One folder rename |
| Scaling team | Multiple devs collide in `services/` | Each owns a module folder |
| Test layout | Tests grouped by layer (less intuitive) | Tests mirror module layout 1:1 |

### Module Conventions

1. **Routers are thin.** No `try/except`, no DB queries, no business logic.
   Just parse params → call service → return schema.
2. **Service is the only place that raises domain exceptions** from
   `<module>/exceptions.py`. Top-level handlers in `main.py` map them to JSON.
3. **No cross-module imports of internal helpers.** Modules talk to each other
   via their `service.py` public functions only — never reach into another
   module's `models.py` directly from a router.
4. **Each module's `models.py` defines its own ORM tables.** Foreign keys
   reference other modules' tables by string (`"users.id"`) to avoid circular
   imports. `src/models.py` re-exports them all so Alembic autogenerate sees
   every table.
5. **Shared infrastructure stays at the top of `src/`** — `database.py`,
   `redis.py`, `config.py`, `logging.py`, `exceptions.py`, `pagination.py`.
6. **Tests mirror modules.** `tests/<module>/test_*.py` — never one giant
   `tests/` folder.

> **Architecture note**: This is a **deliberate departure** from the previous
> "repositories layer" decision in Q2. After comparing the layer-based plan
> with the modular layout in `zhanymkanov/fastapi-best-practices`, modules win
> for a project this size (8 features, 1–2 devs). The Copilot instructions
> file (`.github/copilot-instructions.md`) must be updated accordingly.

---

## 3. Database Design & ERD

> **Source of truth**: [`learning_platform/docs/erd.md`](./erd.md) (DBML format).
> The tables below mirror that file 1:1. If `erd.md` changes, update this section.

### Entities

#### `users`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| role | VARCHAR | NOT NULL — values: `admin`, `instructor`, `student` |
| password | VARCHAR | NOT NULL (bcrypt-hashed) |
| display_name | VARCHAR(255) | NOT NULL, DEFAULT `''` |
| avatar | VARCHAR | nullable (URL to avatar image) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() |

#### `courses`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| instructor | UUID | FK → users.id, NOT NULL |
| title | VARCHAR(255) | UNIQUE, NOT NULL |
| description | VARCHAR | nullable |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() |

#### `lessons`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| course | UUID | FK → courses.id, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| timeline | VARCHAR | nullable (e.g. estimated duration "30 min") |
| content | TEXT | NOT NULL |
| order | INTEGER | NOT NULL — display order within course |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() |

#### `progress`

> Single unified progress table per `(user, lesson)`. Course-level progress is
> derived by aggregating rows for a course.

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| user | UUID | FK → users.id, NOT NULL |
| lesson | UUID | FK → lessons.id, NOT NULL |
| status | VARCHAR | NOT NULL — values: `not_started`, `in_progress`, `completed` |
| accessed_at | TIMESTAMP | NOT NULL, DEFAULT now() |
| completed_at | TIMESTAMP | nullable |

#### `enrollments`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| user | UUID | FK → users.id, NOT NULL |
| course | UUID | FK → courses.id, NOT NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() |

#### `quizzes`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| lesson | UUID | FK → lessons.id, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| description | VARCHAR | nullable |
| time_limit | INTERVAL | nullable (e.g. `'30 minutes'`) |

#### `questions`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| quiz | UUID | FK → quizzes.id, NOT NULL |
| text | TEXT | NOT NULL |
| type | VARCHAR | NOT NULL — values: `mcq`, `text` |
| options | JSON | nullable (array of choice strings for `mcq`) |
| correct_answer | VARCHAR | NOT NULL (canonical correct answer for grading) |

#### `submissions`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| user | UUID | FK → users.id, NOT NULL |
| quiz | UUID | FK → quizzes.id, NOT NULL |
| score | FLOAT | NOT NULL (0–100) |
| submitted_at | TIMESTAMP | NOT NULL, DEFAULT now() |

#### `answers`

| Column | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| submission | UUID | FK → submissions.id, NOT NULL |
| question | UUID | FK → questions.id, NOT NULL |
| text | TEXT | NOT NULL (student's answer — for `mcq` it's the chosen option string) |
| is_correct | BOOLEAN | NOT NULL (computed at submission time) |

### Relationships

| Relationship | Type |
| --- | --- |
| User (instructor) → Courses | 1-N |
| User ↔ Courses | N-N via `enrollments` |
| Course → Lessons | 1-N |
| Lesson → Quiz | 1-N (a lesson may have ≥ 0 quizzes) |
| Quiz → Questions | 1-N |
| User → Submissions | 1-N |
| Submission → Answers | 1-N |
| User + Lesson → Progress | 1-1 |

### RBAC Rules

| Action | Admin | Instructor | Student |
| --- | --- | --- | --- |
| Create/update/delete course | ✅ | ✅ (own) | ❌ |
| Create/update/delete lesson | ✅ | ✅ (own course) | ❌ |
| Create/update/delete quiz | ✅ | ✅ (own course) | ❌ |
| Enroll in course | ❌ | ❌ | ✅ |
| View lesson content | ✅ | ✅ | ✅ (if enrolled) |
| Submit quiz | ❌ | ❌ | ✅ (if enrolled) |
| View own progress | ❌ | ❌ | ✅ |
| Admin CRUD on all entities | ✅ | ❌ | ❌ |

### Lesson Completion Logic

- **Lesson has a quiz** → lesson `progress.status = completed` when the student
  submits a passing score (grading rule defined in `submissions/grading.py`).
- **Lesson has no quiz** → lesson `progress.status = completed` when the student
  visits it (GET `/lessons/{id}`).
- Status transitions: `not_started` → `in_progress` (on first access) →
  `completed` (on satisfying the rule above).
- Course-level progress is **derived** by counting `progress` rows where
  `status = completed` for lessons in that course.

---

## 4. API Design

**Base URL**: `/api/v1`

### Auth Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | ❌ | Register (role defaults to student) |
| POST | `/auth/login` | ❌ | Login → access + refresh tokens |
| POST | `/auth/refresh` | ✅ refresh | Rotate tokens |
| POST | `/auth/logout` | ✅ | Blacklist token in Redis |

### User Endpoints

| Method | Path | Auth | Permission |
|---|---|---|---|
| GET | `/users/me` | ✅ | Self |
| PATCH | `/users/me` | ✅ | Self |

### Course Endpoints

| Method | Path | Auth | Permission |
|---|---|---|---|
| POST | `/courses` | ✅ | Instructor, Admin |
| GET | `/courses` | ✅ | Any (paginated, filterable) |
| GET | `/courses/{id}` | ✅ | Any |
| PATCH | `/courses/{id}` | ✅ | Instructor (own), Admin |
| DELETE | `/courses/{id}` | ✅ | Admin only |
| POST | `/courses/{id}/enroll` | ✅ | Student |

### Lesson Endpoints

| Method | Path | Auth | Permission |
|---|---|---|---|
| POST | `/courses/{course_id}/lessons` | ✅ | Instructor (own course), Admin |
| GET | `/courses/{course_id}/lessons` | ✅ | Any enrolled / Instructor / Admin |
| GET | `/lessons/{id}` | ✅ | Enrolled student, Instructor (own), Admin — triggers "no-quiz" completion |
| PATCH | `/lessons/{id}` | ✅ | Instructor (own course), Admin |
| DELETE | `/lessons/{id}` | ✅ | Instructor (own course), Admin |

### Quiz Endpoints

| Method | Path | Auth | Permission |
|---|---|---|---|
| POST | `/lessons/{lesson_id}/quiz` | ✅ | Instructor (own course), Admin |
| GET | `/lessons/{lesson_id}/quiz` | ✅ | Enrolled student, Instructor, Admin |
| PATCH | `/lessons/{lesson_id}/quiz` | ✅ | Instructor (own course), Admin |
| DELETE | `/lessons/{lesson_id}/quiz` | ✅ | Instructor (own course), Admin |
| POST | `/quizzes/{quiz_id}/questions` | ✅ | Instructor, Admin |
| PATCH | `/questions/{id}` | ✅ | Instructor, Admin |
| DELETE | `/questions/{id}` | ✅ | Instructor, Admin |

### Submission Endpoints

| Method | Path | Auth | Permission |
|---|---|---|---|
| POST | `/quizzes/{quiz_id}/submit` | ✅ | Enrolled student (once per quiz) |
| GET | `/quizzes/{quiz_id}/submission` | ✅ | Own submission |

### Progress Endpoints

| Method | Path | Auth | Permission |
|---|---|---|---|
| GET | `/courses/{course_id}/progress` | ✅ | Own progress (Student) |
| GET | `/progress` | ✅ | All enrolled courses progress |

### Admin Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET/PATCH/DELETE | `/admin/users/{id}` | ✅ Admin | Manage any user |
| GET | `/admin/users` | ✅ Admin | List all users |
| GET/PATCH/DELETE | `/admin/courses/{id}` | ✅ Admin | Manage any course |
| GET | `/admin/courses` | ✅ Admin | List all courses |
| GET/DELETE | `/admin/submissions` | ✅ Admin | View/delete submissions |
| GET | `/admin/progress` | ✅ Admin | View learning records |
| GET | `/admin` | ✅ Admin | SQLAdmin UI (web interface) |

### Common Query Parameters

| Param | Used on | Description |
|---|---|---|
| `limit` | List endpoints | Default 20, max 100 |
| `offset` | List endpoints | Skip N items |
| `search` | Courses | Filter by title/description |
| `instructor` | Courses | Filter by instructor user id |

### Standard Error Response
```json
{
  "detail": "Human-readable message",
  "error_code": "MACHINE_READABLE_CODE"
}
```

### Health Check

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status": "healthy", "db": "ok", "redis": "ok"}` |

---

## 5. Detailed Specs — Schemas (DTOs)

Each module owns its own `schemas.py`. Use Pydantic v2. Field names match the
ORM columns defined in [`erd.md`](./erd.md).

### `auth/schemas.py`

```python
RegisterRequest: email, password, display_name (optional)
LoginRequest: email, password
TokenResponse: access_token, refresh_token, token_type="bearer"
RefreshRequest: refresh_token
```

### `users/schemas.py`

```python
UserResponse: id, email, role, display_name, avatar, created_at
UserUpdateRequest: display_name (optional), avatar (optional), password (optional)
```

### `courses/schemas.py`

```python
CourseCreateRequest: title, description (optional)
CourseUpdateRequest: title (optional), description (optional)
CourseResponse: id, title, description, instructor, created_at, updated_at
CourseListResponse: items: List[CourseResponse], total, limit, offset
EnrollmentResponse: id, user, course, created_at
```

### `lessons/schemas.py`

```python
LessonCreateRequest: title, content, timeline (optional), order (default 0)
LessonUpdateRequest: title (optional), content (optional), timeline (optional), order (optional)
LessonResponse: id, course, title, timeline, content, order, has_quiz, created_at, updated_at
```

### `quizzes/schemas.py`

```python
QuizCreateRequest: title, description (optional), time_limit (optional, ISO-8601 duration)
QuizUpdateRequest: title (optional), description (optional), time_limit (optional)
QuizResponse: id, lesson, title, description, time_limit, question_count
QuizDetailResponse: QuizResponse + questions: List[QuestionStudentResponse]

QuestionCreateRequest: text, type ("mcq" | "text"), options (List[str] for mcq), correct_answer
QuestionUpdateRequest: text (optional), type (optional), options (optional), correct_answer (optional)
QuestionStudentResponse: id, quiz, text, type, options   # correct_answer hidden from students
QuestionAdminResponse:   id, quiz, text, type, options, correct_answer
```

### `submissions/schemas.py`

```python
SubmitQuizRequest: answers: List[AnswerSubmission]
AnswerSubmission: question (UUID), text (str)   # for "mcq" the chosen option string; for "text" the free-text answer
SubmissionResponse: id, quiz, user, score, submitted_at
SubmissionDetailResponse: SubmissionResponse + answers: List[AnswerResultResponse]
AnswerResultResponse: id, question, text, is_correct
```

### `progress/schemas.py`

```python
LessonProgressResponse: lesson, status ("not_started" | "in_progress" | "completed"), accessed_at, completed_at
CourseProgressResponse: course, completed_lessons, total_lessons, percent_complete, is_complete   # derived
CourseProgressListResponse: items: List[CourseProgressResponse]
```

### Shared (`src/pagination.py`, `src/exceptions.py`)

```python
ErrorResponse: detail, error_code
PaginationParams: limit=20, offset=0   # used as a Query dependency
```

---

## 6. Detailed Specs — ORM Models

Each module declares its own tables in `<module>/models.py`. Use SQLAlchemy 2.0
async `mapped_column` style. `src/models.py` re-exports every ORM class so
Alembic autogenerate sees the full metadata.

- All PKs: `UUID`, server_default `gen_random_uuid()` on PostgreSQL; `uuid4()` default for aiosqlite tests.
- All timestamps: `DateTime(timezone=True)`, server_default `func.now()`. `updated_at` uses `onupdate=func.now()` where present in `erd.md`.
- Foreign keys reference other modules' tables **by string** (`ForeignKey("users.id")`) to avoid cross-module imports.
- `quizzes.time_limit` → `Interval`. `questions.options` → `JSON` (nullable; only populated for `type = "mcq"`).
- Enums (string-valued) declared in each module's `models.py` (or a small shared `src/enums.py` if reused):

  ```python
  class UserRole(str, Enum):       admin, instructor, student
  class QuestionType(str, Enum):   mcq, text
  class ProgressStatus(str, Enum): not_started, in_progress, completed
  ```

| Module | ORM classes |
| --- | --- |
| `users/models.py` | `User` |
| `courses/models.py` | `Course`, `Enrollment` |
| `lessons/models.py` | `Lesson` |
| `quizzes/models.py` | `Quiz`, `Question` |
| `submissions/models.py` | `Submission`, `Answer` |
| `progress/models.py` | `Progress` |
| `auth/models.py` | (only if storing refresh-token rows; otherwise empty) |

---

## 7. Detailed Specs — Data Access (Service Layer)

There is **no dedicated repositories layer** in this design (see Section 2).
Each module's `service.py` owns its own SQLAlchemy queries and is the single
entry point for that module's business logic.

### Class-based service pattern

> **Updated per code review (2026-05-04):** All services use a class pattern
> rather than loose functions. This improves testability (mock the class),
> provides shared session via constructor, and creates a clear API surface
> for cross-module calls.

```python
# src/<module>/service.py
class CourseService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, data: CourseCreateRequest) -> Course:
        ...

# src/<module>/dependencies.py
def get_course_service(db: AsyncSession = Depends(get_db)) -> CourseService:
    return CourseService(db)

# src/<module>/router.py
@router.post("/courses")
async def create_course(
    data: CourseCreateRequest,
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    course = await service.create(data)
    return CourseResponse.model_validate(course)
```

### Service responsibilities

- Take `AsyncSession` via **constructor** (not directly from `Depends(get_db)`).
- Build queries with `select()`, `scalars()`, `execute()` — SQLAlchemy 2.0 style.
- Return ORM instances **internally**; routers convert them to response schemas.
- Raise domain exceptions from `<module>/exceptions.py` (never `HTTPException`).
- Never import another module's `models.py` from a router; always go through
  the other module's `service.py`.
- **CPU-bound operations** (e.g., bcrypt) must use
  `asyncio.get_running_loop().run_in_executor(None, ...)` to avoid blocking
  the event loop.

### Cross-module call examples

- `submissions.service.submit(...)` → calls `quizzes.service.get_quiz_with_questions(...)`
  to load the quiz and questions, then calls `progress.service.mark_lesson_completed(...)`.
- `lessons.service.get_lesson_for_student(...)` → on first access calls
  `progress.service.touch(user, lesson)` (transitions `not_started` → `in_progress`,
  or → `completed` for no-quiz lessons).

---

## 8. Detailed Specs — Services

Per-module business logic. Each module's `service.py` only raises exceptions
declared in its own `exceptions.py` (or in the shared `src/exceptions.py`
hierarchy below). Top-level handlers in `main.py` map them to JSON.

### Shared exception hierarchy (`src/exceptions.py`)

```python
class DomainError(Exception): ...
class NotFoundError(DomainError): ...
class AuthorizationError(DomainError): ...
class ConflictError(DomainError): ...
class ValidationError(DomainError): ...
```

Modules subclass these for specifics, e.g. `auth/exceptions.py`:
`InvalidCredentials(AuthorizationError)`, `TokenRevoked(AuthorizationError)`.

### Key service logic

**`auth.service`**:

- `register(data)` → hash password, create user, return access + refresh tokens.
- `login(email, password)` → verify password, return tokens.
- `refresh(refresh_token)` → verify, blacklist old refresh token in Redis, return new pair.
- `logout(access_token)` → add jti to Redis blacklist.

**`courses.service`**:

- `enroll(user_id, course_id)` → check course exists, check not already enrolled, create `Enrollment`.
- (No `publish` flow — `erd.md` has no published flag.)

**`lessons.service`**:

- `get_lesson_for_student(lesson_id, user_id)` → fetch lesson, ensure enrollment,
  call `progress.service.touch(user_id, lesson_id)`. If the lesson has no quiz,
  `touch` sets `status = completed`.

**`quizzes.service`**:

- CRUD for quizzes and questions (instructor/admin only).
- `get_quiz_for_student(quiz_id)` → returns `QuestionStudentResponse` (no `correct_answer`).

**`submissions.service`** (uses helpers in `submissions/grading.py`):

1. Check the user is enrolled in the lesson's course.
2. Load the quiz with all questions.
3. For each answer: build an `Answer` row with `is_correct = grade(question, text)`
   (case-insensitive equality vs `question.correct_answer`).
4. Compute `score = 100 * correct / total`.
5. Persist `Submission` + `Answer` rows.
6. Call `progress.service.mark_lesson_completed(user_id, lesson_id)` if score
   meets the configured pass threshold (default 70 — sourced from `config.py`,
   not stored on the quiz since `erd.md` has no `passing_score`).
7. Return `SubmissionDetailResponse`.

**`progress.service`**:

- `touch(user_id, lesson_id)` → upsert `Progress`; transition `not_started` →
  `in_progress` (and → `completed` for no-quiz lessons).
- `mark_lesson_completed(user_id, lesson_id)` → set `status = completed`, `completed_at = now()`.
- `get_course_progress(user_id, course_id)` → **derive** by counting `Progress`
  rows with `status = completed` over total lessons in the course (no stored
  course-level row; matches `erd.md`).

---

## 9. Task Breakdown

> Paths reflect the **module-based** layout from Section 2. Each phase produces
> one or more self-contained module folders under `src/`.

### Phase 0 — Project Scaffolding

| # | Task |
|---|---|
| 0.1 | Initialize `learning_platform/` with `uv init`; configure `pyproject.toml` with FastAPI, SQLAlchemy 2.0, asyncpg, alembic, pydantic-settings, redis, PyJWT, bcrypt, sqladmin, ruff, pytest, pytest-asyncio, httpx, aiosqlite |
| 0.2 | Create the module-based `src/` tree (auth/, users/, courses/, lessons/, quizzes/, submissions/, progress/, admin/) plus shared `config.py`, `database.py`, `redis.py`, `logging.py`, `exceptions.py`, `pagination.py`, `models.py`, `main.py` |
| 0.3 | Mirror module folders under `tests/`; add `.env.example`, `.gitignore`, `README.md` scaffold |
| 0.4 | `docker-compose.yml` (app + PostgreSQL + Redis) |
| 0.5 | `Dockerfile` (multi-stage; uses `python -m uvicorn` and `python -m alembic`) |
| 0.6 | Alembic init + `env.py` configured for async SQLAlchemy; point `target_metadata` at `src.models` (re-export module) |
| 0.7 | Update `.github/copilot-instructions.md` to reflect the **module-based** architecture (remove the previous "repositories layer" wording) |

✅ **Checkpoint**: `docker compose up` starts app, DB, Redis. `/health` returns 200.

### Phase 1 — Auth & Users

| # | Task |
|---|---|
| 1.1 | `src/config.py` — pydantic-settings (DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALG, access/refresh TTLs, QUIZ_PASS_THRESHOLD) |
| 1.2 | `src/database.py` — async engine, session factory, `Base`, `get_db` dependency |
| 1.3 | `src/redis.py` — async redis client + token blacklist helpers |
| 1.4 | `src/exceptions.py` — `DomainError` hierarchy |
| 1.5 | `users/models.py` — `User` (email, role, password, display_name, avatar, created_at) |
| 1.6 | Alembic migration: create `users` table |
| 1.7 | `auth/security.py` — bcrypt hash/verify; `auth/jwt.py` — encode/decode access + refresh tokens |
| 1.8 | `auth/exceptions.py`, `auth/constants.py`, `auth/schemas.py`, `auth/service.py` |
| 1.9 | `auth/dependencies.py` — `get_current_user`, `require_roles(...)` factory |
| 1.10 | `auth/router.py` — POST `/auth/{register,login,refresh,logout}` |
| 1.11 | `users/schemas.py`, `users/service.py`, `users/router.py` (GET/PATCH `/users/me`) |
| 1.12 | `src/main.py` — app factory, lifespan, global exception handlers, mount auth + users routers |
| 1.13 | `src/models.py` — re-export `User` for Alembic |
| 1.14 | `tests/conftest.py` — async client, aiosqlite in-memory DB, mocked Redis, auth fixtures |
| 1.15 | `tests/auth/test_auth.py` — register, login, refresh, logout, duplicate email |
| 1.16 | `tests/users/test_users.py` — get me, update me, unauthorized |

✅ **Checkpoint**: Register → Login → GET /users/me → Refresh → Logout. Tests pass.

### Phase 2 — Courses, Lessons, Enrollment

| # | Task |
|---|---|
| 2.1 | `courses/models.py` — `Course`, `Enrollment` |
| 2.2 | Alembic migration: `courses`, `enrollments` |
| 2.3 | `courses/schemas.py`, `courses/exceptions.py`, `courses/service.py` |
| 2.4 | `courses/router.py` — CRUD + `POST /courses/{id}/enroll` (no publish flow) |
| 2.5 | `lessons/models.py` — `Lesson` (title, timeline, content, order) |
| 2.6 | Alembic migration: `lessons` |
| 2.7 | `lessons/schemas.py`, `lessons/exceptions.py`, `lessons/service.py` (calls `progress.service.touch` on read) |
| 2.8 | `lessons/router.py` — nested under `/courses/{course_id}/lessons` + `/lessons/{id}` |
| 2.9 | Re-export `Course`, `Enrollment`, `Lesson` from `src/models.py` |
| 2.10 | `tests/courses/test_courses.py`, `tests/lessons/test_lessons.py` |

✅ **Checkpoint**: Create course, add lessons, enroll student, student views lesson (no quiz → auto-complete via progress module).

### Phase 3 — Quizzes, Submissions, Grading

| # | Task |
|---|---|
| 3.1 | `quizzes/models.py` — `Quiz` (time_limit Interval), `Question` (type, options JSON, correct_answer) |
| 3.2 | Alembic migration: `quizzes`, `questions` |
| 3.3 | `quizzes/schemas.py` (student view hides `correct_answer`), `quizzes/service.py`, `quizzes/router.py` |
| 3.4 | `submissions/models.py` — `Submission`, `Answer` |
| 3.5 | Alembic migration: `submissions`, `answers` |
| 3.6 | `submissions/grading.py` — pure helpers: `grade_answer(question, text) -> bool` |
| 3.7 | `submissions/schemas.py`, `submissions/exceptions.py`, `submissions/service.py` (auto-grade + call `progress.service.mark_lesson_completed` when ≥ pass threshold) |
| 3.8 | `submissions/router.py` |
| 3.9 | Re-export new models from `src/models.py` |
| 3.10 | `tests/quizzes/test_quizzes.py` |
| 3.11 | `tests/submissions/test_submissions.py` (mcq, text, partial credit, pass/fail thresholds) |

✅ **Checkpoint**: Submit quiz → auto-graded → lesson `progress.status = completed` (if score ≥ threshold).

### Phase 4 — Progress Tracking

| # | Task |
|---|---|
| 4.1 | `progress/models.py` — `Progress` (user, lesson, status enum, accessed_at, completed_at) |
| 4.2 | Alembic migration: `progress` |
| 4.3 | `progress/schemas.py`, `progress/exceptions.py` |
| 4.4 | `progress/service.py` — `touch`, `mark_lesson_completed`, `get_course_progress` (derives course %) |
| 4.5 | Re-export `Progress` from `src/models.py`; verify `lessons.service` and `submissions.service` already call into `progress.service` |
| 4.6 | `progress/router.py` — `GET /courses/{course_id}/progress`, `GET /progress` |
| 4.7 | `tests/progress/test_progress.py` (no-quiz auto-complete, quiz pass/fail, course % derivation) |

✅ **Checkpoint**: Complete all lessons in a course → derived course progress = 100%, `is_complete = true`.

### Phase 5 — Admin Features

| # | Task |
|---|---|
| 5.1 | `admin/router.py` — REST CRUD under `/api/v1/admin/*` (users, courses, lessons, quizzes, submissions, progress) |
| 5.2 | `admin/views.py` — SQLAdmin `ModelView` per ORM class |
| 5.3 | `admin/auth.py` — SQLAdmin `AuthenticationBackend` reusing `auth/service.py` |
| 5.4 | Mount SQLAdmin at `/admin` in `src/main.py` |
| 5.5 | `tests/admin/test_admin.py` — RBAC (non-admins → 403), CRUD happy paths |

✅ **Checkpoint**: Admin can CRUD all entities via REST API and SQLAdmin UI.

### Phase 6 — Testing & Polish

| # | Task |
|---|---|
| 6.1 | Run coverage report; add missing tests in any `tests/<module>/` to reach ≥ 80% |
| 6.2 | `uv run ruff check src/ tests/` and fix all issues |
| 6.3 | `uv run ruff format src/ tests/` |
| 6.4 | Add Swagger metadata in each `<module>/router.py`: tags, descriptions, example bodies |
| 6.5 | `docs/erd.png` — exported diagram from `erd.md` (DBML) |
| 6.6 | `README.md` — setup instructions, env config, run commands, module map |
| 6.7 | **Create `docs/api/CHANGELOG.md`** — document all endpoints introduced |

✅ **Final Checkpoint**: All tests pass, coverage ≥ 80%, lint clean, Swagger polished, README complete.

---

## 10. Execution Steps (Commands)

```bash
# Setup
cd /Users/khoivo/python-training/python-training/learning_platform
uv sync

# Run DB + Redis (Docker)
docker compose up -d db redis

# Run migrations
uv run python -m alembic upgrade head

# Start app (dev)
uv run python -m uvicorn src.main:app --reload --port 8001

# Run tests
uv run pytest tests/ --tb=short -q

# Run tests with coverage
uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Create new migration
uv run python -m alembic revision --autogenerate -m "description"

# Full Docker stack
docker compose up -d --build
docker compose logs app --tail=50
docker compose down
```

---

## 11. Verification Steps

### After Each Phase
1. `uv run pytest tests/ --tb=short -q` — all tests pass
2. `uv run ruff check src/ tests/` — zero lint errors
3. Manual smoke test via Swagger UI at `http://localhost:8001/docs`

### Final Verification
1. `uv run pytest tests/ --cov=src --cov-report=term-missing` — coverage ≥ 80%
2. `uv run ruff check src/ tests/` — clean
3. `docker compose up -d --build && curl http://localhost:8001/health` — `{"status":"healthy"}`
4. Check Swagger UI renders all endpoints with tags and examples
5. Verify SQLAdmin accessible at `http://localhost:8001/admin`
6. Confirm `docs/api/CHANGELOG.md` exists and documents all endpoints

---

## 12. Error Tracking Protocol

> **If any mistake occurs during implementation:**
>
> 1. **Log it** in `gotchas.md` (project root) — include the symptom, root cause, and fix
> 2. **Update `.claude/CLAUDE.md`** (if it exists) with the corrected rule
> 3. **Update `.github/copilot-instructions.md`** with the corrected rule so it applies to all future executions

Examples of things that must be logged:
- SQLAlchemy async session misuse (e.g. using sync `.all()` instead of `await session.execute(select(...))`)
- aiosqlite vs PostgreSQL UUID type incompatibilities in tests
- JWT token decode errors (algorithm mismatch)
- Redis connection issues in test environment (must be mocked or skipped)
- SQLAdmin incompatibility with async session factory

---

## 13. Post-Implementation: API Changelog

After all phases are complete, create `docs/api/CHANGELOG.md` with:

```markdown
# API Changelog

## v1.0.0 — [DATE]

### Auth
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- POST /api/v1/auth/refresh
- POST /api/v1/auth/logout

### Users
- GET /api/v1/users/me
- PATCH /api/v1/users/me

### Courses
- POST /api/v1/courses
- GET /api/v1/courses
- GET /api/v1/courses/{id}
- PATCH /api/v1/courses/{id}
- DELETE /api/v1/courses/{id}
- POST /api/v1/courses/{id}/enroll

### Lessons
- POST /api/v1/courses/{course_id}/lessons
- GET /api/v1/courses/{course_id}/lessons
- GET /api/v1/lessons/{id}
- PATCH /api/v1/lessons/{id}
- DELETE /api/v1/lessons/{id}

### Quizzes
- POST /api/v1/lessons/{lesson_id}/quiz
- GET /api/v1/lessons/{lesson_id}/quiz
- PATCH /api/v1/lessons/{lesson_id}/quiz
- DELETE /api/v1/lessons/{lesson_id}/quiz
- POST /api/v1/quizzes/{quiz_id}/questions
- PATCH /api/v1/questions/{id}
- DELETE /api/v1/questions/{id}

### Submissions
- POST /api/v1/quizzes/{quiz_id}/submit
- GET /api/v1/quizzes/{quiz_id}/submission

### Progress
- GET /api/v1/courses/{course_id}/progress
- GET /api/v1/progress

### Admin
- GET/PATCH/DELETE /api/v1/admin/users/{id}
- GET /api/v1/admin/users
- GET/PATCH/DELETE /api/v1/admin/courses/{id}
- GET /api/v1/admin/courses
- GET/DELETE /api/v1/admin/submissions
- GET /api/v1/admin/progress
- GET /admin (SQLAdmin UI)

### System
- GET /health
```

---

## 14. Instruction File Updates Needed

The following files must be updated as part of Phase 0:

### `.github/copilot-instructions.md`

Add/update:

- **Architecture section**: replace the previous "repositories layer" wording —
  `learning_platform` now uses a **module-by-feature** layout
  (`src/<feature>/{router,service,models,schemas,exceptions,dependencies}.py`)
  following [zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices#project-structure).
  There is **no** `repositories/`, `domain/services/`, or `api/v1/` folder —
  each module owns its own queries inside `service.py`.
- Add a rule: **no cross-module imports of internal helpers** — modules talk to
  each other only via their `service.py` public functions.
- Add a rule: each module's `models.py` defines its own ORM tables;
  `src/models.py` re-exports them all so Alembic autogenerate sees every table.
- Add `Redis` to the tech stack table.
- Add `SQLAdmin` to the tech stack table.
- Update "Async everywhere" rule to include Redis operations.

---

## 15. Estimation Summary

| Phase | Scope | Est. Hours |
|---|---|---|
| Phase 0 | Scaffolding, Docker, Alembic, instruction update | 3h |
| Phase 1 | Auth, Users, JWT + Redis blacklist | 8h |
| Phase 2 | Courses, Lessons, Enrollment | 8h |
| Phase 3 | Quizzes, Submissions, Auto-grading | 10h |
| Phase 4 | Progress Tracking | 5h |
| Phase 5 | Admin APIs + SQLAdmin UI | 5h |
| Phase 6 | Testing ≥ 80%, lint, polish, changelog | 6h |
| **Total** | | **~45h (~6 working days)** |
