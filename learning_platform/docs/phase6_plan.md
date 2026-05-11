# Phase 6 — Testing & Polish

**Target Agent**: Claude Sonnet 4.6 (or equivalent)
**Prerequisites**: Phase 0–5 completed. All modules implemented and tests passing.
**Branch**: `feat/implement-courses-lessons-enrollment`

---

## Context for Agent

### Goal
Reach ≥80% test coverage, clean linting, polished Swagger docs, complete README, and create the API changelog.

### What Already Exists
- All modules implemented: auth, users, courses, lessons, quizzes, submissions, progress, admin
- Tests in each `tests/<module>/` directory
- `gotchas.md` with known issues
- `.claude/CLAUDE.md` with agent rules
- `docs/analysys_plan.md` with full API spec

---

## Execution Steps

### Step 6.1 — Coverage Gap Analysis

Run coverage report:
```bash
uv run pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

Review the `term-missing` output. For each module below 80%:
1. Identify uncovered lines (service edge cases, error paths, exception branches)
2. Write targeted tests to cover them
3. Re-run until ≥80%

Common gaps to check:
- Service methods not called from any test (e.g. `list_all`, edge cases)
- Error paths: invalid IDs, missing fields, empty lists
- Cross-module integration: progress triggered by quiz submission
- Config edge cases: QUIZ_PASS_THRESHOLD boundary (exactly 70%)
- Exception branches in auth (expired, revoked, invalid tokens)

---

### Step 6.2 — Lint & Format

```bash
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/
```

Fix all remaining issues. The only pre-existing lint warning is `A005` on `src/logging.py` (shadows stdlib) — this is acceptable, ignore it.

Common issues to watch for:
- Unused imports (F401 on non-`__init__` files)
- Import ordering (I001)
- Line length > 99 chars
- Missing type hints

---

### Step 6.3 — Swagger Metadata

**Modify** `src/main.py` — enhance FastAPI app config:

```python
app = FastAPI(
    title="AI-Enhanced Learning Platform",
    version="1.0.0",
    description="REST API for course management, lessons, quizzes, and progress tracking.",
    openapi_tags=[
        {"name": "auth", "description": "Authentication & token management"},
        {"name": "users", "description": "User profile management"},
        {"name": "courses", "description": "Course CRUD, discovery & enrollment"},
        {"name": "lessons", "description": "Lesson management within courses"},
        {"name": "quizzes", "description": "Quiz & question management"},
        {"name": "submissions", "description": "Quiz submission & auto-grading"},
        {"name": "progress", "description": "Learning progress tracking"},
        {"name": "admin", "description": "Admin CRUD operations"},
        {"name": "system", "description": "Health checks & system info"},
    ],
)
```

**Modify** each `<module>/router.py` — add `summary` and `description` to each endpoint decorator if not already present. Example:
```python
@router.post("", response_model=CourseResponse, status_code=201,
             summary="Create a new course",
             description="Instructors and admins can create courses.")
```

---

### Step 6.4 — Complete README.md

**Modify** `README.md` — add/update these sections:

1. **Project Description** — what this API does
2. **Tech Stack** — table from analysys_plan.md Section 1
3. **Module Map** — what each module under `src/` does
4. **Setup Instructions**:
   - Clone, `uv sync`
   - Copy `.env.example` → `.env`
   - `docker compose up -d db redis`
   - `uv run python -m alembic upgrade head`
   - `uv run python -m uvicorn src.main:app --reload --port 8001`
5. **Running Tests**: `uv run pytest tests/ --tb=short -q`
6. **Running Lint**: `uv run ruff check src/ tests/`
7. **API Documentation**: visit `/docs` (Swagger) or `/redoc`
8. **Admin Panel**: visit `/admin`
9. **Deployment**: Railway with `Dockerfile.railway.learning_platform`

---

### Step 6.5 — Create API Changelog

**Create** `docs/api/CHANGELOG.md`:

```markdown
# API Changelog

## v1.0.0 — Initial Release

### Auth
- POST /api/v1/auth/register — Register new user (defaults to student)
- POST /api/v1/auth/login — Login with email/password → tokens
- POST /api/v1/auth/refresh — Rotate access + refresh tokens
- POST /api/v1/auth/logout — Blacklist current access token

### Users
- GET /api/v1/users/me — Get authenticated user profile
- PATCH /api/v1/users/me — Update own profile

### Courses
- POST /api/v1/courses — Create course (Instructor/Admin)
- GET /api/v1/courses — List courses (paginated, filterable)
- GET /api/v1/courses/{id} — Get course details
- PATCH /api/v1/courses/{id} — Update course (owner/Admin)
- DELETE /api/v1/courses/{id} — Delete course (Admin only)
- POST /api/v1/courses/{id}/enroll — Enroll in course (Student)

### Lessons
- POST /api/v1/courses/{course_id}/lessons — Create lesson (Instructor/Admin)
- GET /api/v1/courses/{course_id}/lessons — List lessons in course
- GET /api/v1/lessons/{id} — Get lesson (triggers progress for students)
- PATCH /api/v1/lessons/{id} — Update lesson (owner/Admin)
- DELETE /api/v1/lessons/{id} — Delete lesson (owner/Admin)

### Quizzes
- POST /api/v1/lessons/{lesson_id}/quiz — Create quiz (Instructor/Admin)
- GET /api/v1/lessons/{lesson_id}/quiz — Get quiz with questions
- PATCH /api/v1/lessons/{lesson_id}/quiz — Update quiz
- DELETE /api/v1/lessons/{lesson_id}/quiz — Delete quiz
- POST /api/v1/quizzes/{quiz_id}/questions — Add question
- PATCH /api/v1/questions/{id} — Update question
- DELETE /api/v1/questions/{id} — Delete question

### Submissions
- POST /api/v1/quizzes/{quiz_id}/submit — Submit quiz (Student, enrolled)
- GET /api/v1/quizzes/{quiz_id}/submission — Get own submission

### Progress
- GET /api/v1/courses/{course_id}/progress — Course progress (Student)
- GET /api/v1/progress — All courses progress (Student)

### Admin
- GET /api/v1/admin/users — List all users
- GET/PATCH/DELETE /api/v1/admin/users/{id} — Manage user
- GET /api/v1/admin/courses — List all courses
- GET/PATCH/DELETE /api/v1/admin/courses/{id} — Manage course
- GET/DELETE /api/v1/admin/submissions — Manage submissions
- GET /api/v1/admin/progress — View all progress
- GET /admin — SQLAdmin UI

### System
- GET /health — Health check
```

---

### Step 6.6 — Final Verification

Run these commands and verify all pass:

```bash
# All tests pass
uv run pytest tests/ --tb=short -q

# Coverage ≥ 80%
uv run pytest tests/ -v --cov=src --cov-report=term-missing

# Zero lint errors (except A005 on logging.py — acceptable)
uv run ruff check src/ tests/

# Docker build works
docker compose up -d --build
curl http://localhost:8001/health
# Expected: {"status":"healthy"}

# Swagger UI renders all endpoints
# Check http://localhost:8001/docs

# SQLAdmin accessible
# Check http://localhost:8001/admin

# Changelog exists
cat docs/api/CHANGELOG.md
```

---

### Step 6.7 — Final Error Tracking Review

Review `gotchas.md` for all entries added during phases 2–5. Ensure each one is reflected in:
- `.claude/CLAUDE.md` — add as a rule if applicable
- `.github/copilot-instructions.md` — create this file if it doesn't exist; add applicable rules

---

## Checkpoint
✅ All tests pass, coverage ≥ 80%, lint clean, Swagger polished, README complete, API changelog created, instruction files updated.
