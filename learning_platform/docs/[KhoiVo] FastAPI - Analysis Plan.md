# AI-Enhanced Learning Platform — Analysis & Implementation Plan

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

### Layer Responsibilities

```
src/
├── api/v1/              # Route handlers — thin, NO try/except, NO business logic
│   ├── auth.py
│   ├── users.py
│   ├── courses.py
│   ├── lessons.py
│   ├── quizzes.py
│   ├── submissions.py
│   ├── progress.py
│   └── admin.py
├── core/
│   ├── config.py        # Settings (pydantic-settings)
│   ├── security.py      # bcrypt, JWT create/decode, refresh token logic
│   └── permissions.py   # RBAC dependency helpers
├── domain/
│   ├── exceptions.py    # DomainError hierarchy
│   ├── models/          # SQLAlchemy async ORM models (one file per entity)
│   └── services/        # Business logic; raises domain exceptions
├── repositories/        # Data access layer (ABCs + concrete implementations)
│   ├── base.py
│   ├── user_repository.py
│   ├── course_repository.py
│   ├── lesson_repository.py
│   ├── quiz_repository.py
│   ├── question_repository.py
│   ├── submission_repository.py
│   └── progress_repository.py
├── schemas/             # Pydantic request/response DTOs
│   ├── auth.py
│   ├── user.py
│   ├── course.py
│   ├── lesson.py
│   ├── quiz.py
│   ├── question.py
│   ├── submission.py
│   ├── progress.py
│   └── common.py        # Pagination, error response
├── infrastructure/
│   ├── database.py      # Async engine, session factory
│   ├── redis.py         # Redis connection + helpers
│   ├── logging.py       # structlog config
│   └── email.py         # Simulated email (background tasks)
├── admin/               # SQLAdmin views
│   └── views.py
└── main.py              # App factory, lifespan, global exception handlers
```

> **Architecture note**: This project uses `repositories/` as a distinct top-level layer (not nested under `domain/`). This differs from the `fast_api_practice` project and reflects the decision in Q2. The Copilot instructions file (`.github/copilot-instructions.md`) must be updated to reflect this.

---

## 3. Database Design & ERD

### Entities

#### `users`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| username | VARCHAR(100) | UNIQUE, NOT NULL |
| hashed_password | VARCHAR | NOT NULL |
| full_name | VARCHAR(255) | |
| role | ENUM (admin, instructor, student) | NOT NULL, DEFAULT student |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() |

#### `courses`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | |
| instructor_id | UUID | FK → users.id, NOT NULL |
| is_published | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

#### `enrollments` (many-to-many: students ↔ courses)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| student_id | UUID | FK → users.id, NOT NULL |
| course_id | UUID | FK → courses.id, NOT NULL |
| enrolled_at | TIMESTAMP | NOT NULL |
| UNIQUE | | (student_id, course_id) |

#### `lessons`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| course_id | UUID | FK → courses.id, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| content | TEXT | NOT NULL (text-only, no multimedia) |
| order_index | INTEGER | NOT NULL, DEFAULT 0 |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

#### `quizzes`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| lesson_id | UUID | FK → lessons.id, UNIQUE, NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| passing_score | INTEGER | NOT NULL, DEFAULT 70 (percent) |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

#### `questions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| quiz_id | UUID | FK → quizzes.id, NOT NULL |
| text | TEXT | NOT NULL |
| question_type | ENUM (single_choice, multiple_choice) | NOT NULL |
| order_index | INTEGER | NOT NULL, DEFAULT 0 |

#### `answer_options`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| question_id | UUID | FK → questions.id, NOT NULL |
| text | TEXT | NOT NULL |
| is_correct | BOOLEAN | NOT NULL, DEFAULT false |

#### `submissions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| student_id | UUID | FK → users.id, NOT NULL |
| quiz_id | UUID | FK → quizzes.id, NOT NULL |
| score | FLOAT | NOT NULL (0–100) |
| passed | BOOLEAN | NOT NULL |
| submitted_at | TIMESTAMP | NOT NULL |
| UNIQUE | | (student_id, quiz_id) — one attempt per quiz |

#### `submission_answers`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| submission_id | UUID | FK → submissions.id, NOT NULL |
| question_id | UUID | FK → questions.id, NOT NULL |
| selected_option_ids | UUID[] | NOT NULL (array of answer_option ids) |

#### `lesson_progress`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| student_id | UUID | FK → users.id, NOT NULL |
| lesson_id | UUID | FK → lessons.id, NOT NULL |
| completed | BOOLEAN | NOT NULL, DEFAULT false |
| completed_at | TIMESTAMP | nullable |
| UNIQUE | | (student_id, lesson_id) |

#### `course_progress`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| student_id | UUID | FK → users.id, NOT NULL |
| course_id | UUID | FK → courses.id, NOT NULL |
| completed_lessons | INTEGER | NOT NULL, DEFAULT 0 |
| total_lessons | INTEGER | NOT NULL |
| percent_complete | FLOAT | NOT NULL, DEFAULT 0.0 |
| is_complete | BOOLEAN | NOT NULL, DEFAULT false |
| UNIQUE | | (student_id, course_id) |

### Relationships
| Relationship | Type |
|---|---|
| User (instructor) → Courses | 1-N |
| User (student) ↔ Courses | N-N via `enrollments` |
| Course → Lessons | 1-N |
| Lesson → Quiz | 1-1 (optional) |
| Quiz → Questions | 1-N |
| Question → AnswerOptions | 1-N |
| Student → Submissions | 1-N |
| Submission → SubmissionAnswers | 1-N |
| Student + Lesson → LessonProgress | 1-1 |
| Student + Course → CourseProgress | 1-1 |

### RBAC Rules

| Action | Admin | Instructor | Student |
|---|---|---|---|
| Create/update/delete course | ✅ | ✅ (own) | ❌ |
| Publish course | ✅ | ✅ (own) | ❌ |
| Create/update/delete lesson | ✅ | ✅ (own course) | ❌ |
| Create/update/delete quiz | ✅ | ✅ (own course) | ❌ |
| Enroll in course | ❌ | ❌ | ✅ |
| View lesson content | ✅ | ✅ | ✅ (if enrolled) |
| Submit quiz | ❌ | ❌ | ✅ (if enrolled) |
| View own progress | ❌ | ❌ | ✅ |
| Admin CRUD on all entities | ✅ | ❌ | ❌ |

### Lesson Completion Logic
- **Lesson has a quiz** → lesson is marked complete when the student **passes** the quiz (score ≥ passing_score)
- **Lesson has no quiz** → lesson is marked complete when the student **visits** it (GET /lessons/{id})
- Course progress is **recalculated** after any lesson completion event

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
| POST | `/courses/{id}/publish` | ✅ | Instructor (own), Admin |
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
| `is_published` | Courses | Filter published/unpublished |
| `instructor_id` | Courses | Filter by instructor |

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

All DTOs live in `src/schemas/`. Use Pydantic v2.

### `schemas/auth.py`
```python
RegisterRequest: email, username, password, full_name (optional)
LoginRequest: email, password
TokenResponse: access_token, refresh_token, token_type="bearer"
RefreshRequest: refresh_token
```

### `schemas/user.py`
```python
UserResponse: id, email, username, full_name, role, is_active, created_at
UserUpdateRequest: full_name (optional), email (optional), password (optional)
```

### `schemas/course.py`
```python
CourseCreateRequest: title, description (optional)
CourseUpdateRequest: title (optional), description (optional)
CourseResponse: id, title, description, instructor_id, is_published, created_at
CourseListResponse: items: List[CourseResponse], total, limit, offset
```

### `schemas/lesson.py`
```python
LessonCreateRequest: title, content, order_index (optional, default 0)
LessonUpdateRequest: title (optional), content (optional), order_index (optional)
LessonResponse: id, course_id, title, content, order_index, has_quiz, created_at
```

### `schemas/quiz.py`
```python
QuizCreateRequest: title, passing_score (default 70)
QuizUpdateRequest: title (optional), passing_score (optional)
QuizResponse: id, lesson_id, title, passing_score, question_count
QuizDetailResponse: QuizResponse + questions: List[QuestionResponse]

QuestionCreateRequest: text, question_type, options: List[AnswerOptionCreateRequest], order_index
AnswerOptionCreateRequest: text, is_correct
QuestionUpdateRequest: text (optional), options (optional), order_index (optional)
QuestionResponse: id, quiz_id, text, question_type, order_index, options
AnswerOptionResponse: id, text  # is_correct NOT exposed to students
AnswerOptionAdminResponse: id, text, is_correct  # instructor/admin only
```

### `schemas/submission.py`
```python
SubmitQuizRequest: answers: List[AnswerSubmission]
AnswerSubmission: question_id, selected_option_ids: List[UUID]
SubmissionResponse: id, quiz_id, score, passed, submitted_at
SubmissionDetailResponse: SubmissionResponse + answers: List[AnswerResultResponse]
AnswerResultResponse: question_id, selected_option_ids, is_correct
```

### `schemas/progress.py`
```python
LessonProgressResponse: lesson_id, completed, completed_at
CourseProgressResponse: course_id, completed_lessons, total_lessons, percent_complete, is_complete
CourseProgressListResponse: items: List[CourseProgressResponse]
```

### `schemas/common.py`
```python
ErrorResponse: detail, error_code
PaginationParams: limit=20, offset=0 (as Query dependency)
```

---

## 6. Detailed Specs — ORM Models

All models in `src/domain/models/`. Use SQLAlchemy 2.0 async mapped_column style.

- All PKs: `UUID`, server_default `gen_random_uuid()` (PostgreSQL) / `uuid4()` for SQLite tests
- All timestamps: `DateTime(timezone=True)`, server_default `func.now()`
- Enums defined in `src/domain/models/enums.py`:
  ```python
  class UserRole(str, Enum): admin, instructor, student
  class QuestionType(str, Enum): single_choice, multiple_choice
  ```

---

## 7. Detailed Specs — Repository Layer

`src/repositories/base.py` — Generic async ABC:
```python
class BaseRepository(ABC):
    async def get_by_id(id) -> T | None
    async def list(**filters) -> list[T]
    async def create(data) -> T
    async def update(id, data) -> T
    async def delete(id) -> None
```

Each concrete repository (`UserRepository`, `CourseRepository`, etc.):
- Takes `AsyncSession` via constructor
- Uses `select()`, `scalars()`, `execute()` — SQLAlchemy 2.0 style
- Returns ORM model instances (services convert to schema responses)

---

## 8. Detailed Specs — Services

`src/domain/services/` — Business logic only; raise domain exceptions from `src/domain/exceptions.py`.

### Exceptions
```python
class DomainError(Exception): ...
class NotFoundError(DomainError): ...
class AuthorizationError(DomainError): ...
class ConflictError(DomainError): ...
class ValidationError(DomainError): ...
```

### Key Service Logic

**`AuthService`**:
- `register(data)` → hash password, create user, return tokens
- `login(email, password)` → verify password, return tokens
- `refresh(refresh_token)` → verify, blacklist old token in Redis, return new tokens
- `logout(access_token)` → add token to Redis blacklist

**`CourseService`**:
- `enroll(student_id, course_id)` → check published, check not already enrolled, create enrollment, create CourseProgress record

**`LessonService`**:
- `get_lesson(lesson_id, student_id)` → fetch lesson; if no quiz → mark lesson complete + update course progress

**`SubmissionService`**:
- `submit(student_id, quiz_id, answers)`:
  1. Check enrolled
  2. Check no prior submission (unique constraint)
  3. Auto-grade: for each question, compare selected options vs correct options
  4. Compute score (percent correct)
  5. Check passed (score ≥ quiz.passing_score)
  6. Save submission + answers
  7. If passed → mark lesson complete → update course progress
  8. Return submission result

**`ProgressService`**:
- `get_course_progress(student_id, course_id)` → fetch CourseProgress record
- `recalculate(student_id, course_id)` → count completed lessons / total lessons, update percent, set is_complete

---

## 9. Task Breakdown

### Phase 0 — Project Scaffolding
| # | Task |
|---|---|
| 0.1 | Initialize `learning_platform/` with `uv init`, configure `pyproject.toml` with all dependencies |
| 0.2 | Create full directory structure (src/, tests/, alembic/, docs/) |
| 0.3 | `.env.example`, `.gitignore`, `README.md` scaffold |
| 0.4 | `docker-compose.yml` (app + PostgreSQL + Redis) |
| 0.5 | `Dockerfile` (multi-stage, uses `python -m uvicorn` and `python -m alembic`) |
| 0.6 | Alembic init + `env.py` configured for async SQLAlchemy |
| 0.7 | Update `.github/copilot-instructions.md` to reflect repositories layer architecture |

✅ **Checkpoint**: `docker compose up` starts app, DB, Redis. `/health` returns 200.

### Phase 1 — Auth & Users
| # | Task |
|---|---|
| 1.1 | `src/core/config.py` — pydantic-settings with DATABASE_URL, REDIS_URL, JWT_SECRET, etc. |
| 1.2 | `src/infrastructure/database.py` — async engine + session factory + `get_db` dependency |
| 1.3 | `src/infrastructure/redis.py` — aioredis connection + token blacklist helpers |
| 1.4 | `src/domain/models/user.py` — User ORM model |
| 1.5 | Alembic migration: create users table |
| 1.6 | `src/core/security.py` — bcrypt hash/verify, JWT access + refresh token create/decode |
| 1.7 | `src/repositories/user_repository.py` |
| 1.8 | `src/domain/exceptions.py` — DomainError hierarchy |
| 1.9 | `src/domain/services/auth_service.py` |
| 1.10 | `src/schemas/auth.py`, `src/schemas/user.py` |
| 1.11 | `src/api/v1/auth.py` — POST /auth/register, /login, /refresh, /logout |
| 1.12 | `src/api/v1/users.py` — GET/PATCH /users/me |
| 1.13 | `src/core/permissions.py` — `require_role()` dependency factory |
| 1.14 | `src/main.py` — app factory, lifespan, global exception handlers, routers |
| 1.15 | `tests/conftest.py` — async client, aiosqlite in-memory DB, auth fixtures |
| 1.16 | `tests/test_auth.py` — register, login, refresh, logout, duplicate email |
| 1.17 | `tests/test_users.py` — get me, update me, unauthorized |

✅ **Checkpoint**: Register → Login → GET /users/me → Refresh → Logout. Tests pass.

### Phase 2 — Courses, Lessons, Enrollment
| # | Task |
|---|---|
| 2.1 | ORM models: Course, Enrollment |
| 2.2 | Alembic migration: courses, enrollments |
| 2.3 | `src/repositories/course_repository.py` |
| 2.4 | `src/domain/services/course_service.py` |
| 2.5 | `src/schemas/course.py` |
| 2.6 | `src/api/v1/courses.py` — full CRUD + publish + enroll |
| 2.7 | ORM model: Lesson |
| 2.8 | Alembic migration: lessons |
| 2.9 | `src/repositories/lesson_repository.py` |
| 2.10 | `src/domain/services/lesson_service.py` (includes no-quiz completion trigger) |
| 2.11 | `src/schemas/lesson.py` |
| 2.12 | `src/api/v1/lessons.py` |
| 2.13 | `tests/test_courses.py` |
| 2.14 | `tests/test_lessons.py` |

✅ **Checkpoint**: Create course, add lessons, enroll student, student views lesson (no quiz → auto complete).

### Phase 3 — Quizzes, Submissions, Grading
| # | Task |
|---|---|
| 3.1 | ORM models: Quiz, Question, AnswerOption |
| 3.2 | Alembic migration: quizzes, questions, answer_options |
| 3.3 | `src/repositories/quiz_repository.py`, `question_repository.py` |
| 3.4 | `src/domain/services/quiz_service.py` |
| 3.5 | `src/schemas/quiz.py` (student view hides is_correct) |
| 3.6 | `src/api/v1/quizzes.py` |
| 3.7 | ORM models: Submission, SubmissionAnswer |
| 3.8 | Alembic migration: submissions, submission_answers |
| 3.9 | `src/repositories/submission_repository.py` |
| 3.10 | `src/domain/services/submission_service.py` (auto-grade + lesson completion trigger) |
| 3.11 | `src/schemas/submission.py` |
| 3.12 | `src/api/v1/submissions.py` |
| 3.13 | `tests/test_quizzes.py` |
| 3.14 | `tests/test_submissions.py` (single choice, multiple choice, pass/fail, duplicate submit) |

✅ **Checkpoint**: Submit quiz → auto-graded → lesson marked complete (if passed).

### Phase 4 — Progress Tracking
| # | Task |
|---|---|
| 4.1 | ORM models: LessonProgress, CourseProgress |
| 4.2 | Alembic migration: lesson_progress, course_progress |
| 4.3 | `src/repositories/progress_repository.py` |
| 4.4 | `src/domain/services/progress_service.py` (recalculate logic) |
| 4.5 | Hook progress recalculation into `LessonService` and `SubmissionService` |
| 4.6 | `src/schemas/progress.py` |
| 4.7 | `src/api/v1/progress.py` |
| 4.8 | `tests/test_progress.py` |

✅ **Checkpoint**: Complete all lessons in a course → course progress = 100%, is_complete = true.

### Phase 5 — Admin Features
| # | Task |
|---|---|
| 5.1 | `src/api/v1/admin.py` — Admin CRUD for users, courses, lessons, quizzes, submissions, progress |
| 5.2 | `src/admin/views.py` — SQLAdmin views for all entities |
| 5.3 | Mount SQLAdmin at `/admin` in `main.py` |
| 5.4 | `tests/test_admin.py` — test RBAC (non-admins get 403) |

✅ **Checkpoint**: Admin can CRUD all entities via REST API and SQLAdmin UI.

### Phase 6 — Testing & Polish
| # | Task |
|---|---|
| 6.1 | Run coverage report; add missing tests to reach ≥ 80% |
| 6.2 | Run `uv run ruff check src/ tests/` and fix all issues |
| 6.3 | Run `uv run ruff format src/ tests/` |
| 6.4 | Add Swagger metadata: tags, descriptions, example bodies |
| 6.5 | `docs/erd.png` — ER diagram image |
| 6.6 | `README.md` — setup instructions, env config, run commands |
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
