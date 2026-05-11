# Phase 5 — Admin Features

**Target Agent**: Claude Sonnet 4.6 (or equivalent)
**Prerequisites**: Phase 0–4 completed. All modules (auth, users, courses, lessons, quizzes, submissions, progress) working.
**Branch**: `feat/implement-courses-lessons-enrollment`

---

## Context for Agent

### What Already Exists
- `src/admin/` — empty module with only `__init__.py`
- `tests/admin/` — empty with only `__init__.py`
- All ORM models: User, Course, Enrollment, Lesson, Quiz, Question, Submission, Answer, Progress
- `require_roles("admin")` dependency works — returns 401 if user lacks the role
- `src/config.py` has `JWT_SECRET` — reuse for SQLAdmin session middleware

### What This Phase Adds
1. **Admin REST API** — CRUD endpoints under `/api/v1/admin/*` for managing all entities
2. **SQLAdmin UI** — web-based admin panel mounted at `/admin`

### Established Patterns
Same as previous phases. Key addition: Admin router reuses existing service classes — no new business logic needed. The admin router just skips ownership checks.

---

## Execution Steps

### Step 5.1 — Admin REST Router

**Create** `src/admin/router.py`:

All endpoints require `Depends(require_roles("admin"))`. Reuse existing services.

| Method | Path | Service Used | Notes |
|--------|------|-------------|-------|
| GET | `/admin/users` | UserService | List all users (add a `list_all` method) |
| GET | `/admin/users/{id}` | UserService | `get_by_id` |
| PATCH | `/admin/users/{id}` | UserService | `update_profile` |
| DELETE | `/admin/users/{id}` | — | Direct delete via session |
| GET | `/admin/courses` | CourseService | `list_courses` (no filters) |
| GET | `/admin/courses/{id}` | CourseService | `get_by_id` |
| PATCH | `/admin/courses/{id}` | CourseService | `update` (admin role skips ownership) |
| DELETE | `/admin/courses/{id}` | CourseService | `delete` |
| GET | `/admin/submissions` | SubmissionService | Add `list_all` method |
| DELETE | `/admin/submissions/{id}` | — | Direct delete |
| GET | `/admin/progress` | ProgressService | Add `list_all` method |

**Required service additions** (add to existing services):
- `UserService.list_all(limit, offset)` → list users with pagination
- `SubmissionService.list_all(limit, offset)` → list all submissions
- `ProgressService.list_all(limit, offset)` → list all progress records

---

### Step 5.2 — Admin Dependencies

**Create** `src/admin/dependencies.py`:

```python
"""Admin Dependencies — DI factories."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
# Import all service classes needed by admin router
```

May just reuse existing `get_*_service()` factories from each module.

---

### Step 5.3 — SQLAdmin ModelViews

**Create** `src/admin/views.py`:

```python
"""SQLAdmin ModelView configurations."""

from sqladmin import ModelView

from src.courses.models import Course, Enrollment
from src.lessons.models import Lesson
from src.progress.models import Progress
from src.quizzes.models import Question, Quiz
from src.submissions.models import Answer, Submission
from src.users.models import User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.role, User.display_name, User.created_at]
    column_searchable_list = [User.email, User.display_name]
    can_create = True
    can_edit = True
    can_delete = True
    name = "User"
    name_plural = "Users"


class CourseAdmin(ModelView, model=Course):
    column_list = [Course.id, Course.title, Course.instructor_id, Course.created_at]
    column_searchable_list = [Course.title]
    name = "Course"
    name_plural = "Courses"


class EnrollmentAdmin(ModelView, model=Enrollment):
    column_list = [Enrollment.id, Enrollment.user_id, Enrollment.course_id, Enrollment.created_at]
    name = "Enrollment"
    name_plural = "Enrollments"


class LessonAdmin(ModelView, model=Lesson):
    column_list = [Lesson.id, Lesson.course_id, Lesson.title, Lesson.order]
    column_searchable_list = [Lesson.title]
    name = "Lesson"
    name_plural = "Lessons"


class QuizAdmin(ModelView, model=Quiz):
    column_list = [Quiz.id, Quiz.lesson_id, Quiz.title]
    name = "Quiz"
    name_plural = "Quizzes"


class QuestionAdmin(ModelView, model=Question):
    column_list = [Question.id, Question.quiz_id, Question.text, Question.type]
    name = "Question"
    name_plural = "Questions"


class SubmissionAdmin(ModelView, model=Submission):
    column_list = [Submission.id, Submission.user_id, Submission.quiz_id, Submission.score]
    name = "Submission"
    name_plural = "Submissions"


class AnswerAdmin(ModelView, model=Answer):
    column_list = [Answer.id, Answer.submission_id, Answer.question_id, Answer.is_correct]
    name = "Answer"
    name_plural = "Answers"


class ProgressAdmin(ModelView, model=Progress):
    column_list = [Progress.id, Progress.user_id, Progress.lesson_id, Progress.status]
    name = "Progress"
    name_plural = "Progress Records"
```

---

### Step 5.4 — SQLAdmin Auth Backend

**Create** `src/admin/auth.py`:

```python
"""SQLAdmin AuthenticationBackend — reuses JWT auth for admin access."""

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request


class AdminAuthBackend(AuthenticationBackend):
    """Session-based auth for SQLAdmin UI. Only admin users can access."""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username", "")
        password = form.get("password", "")

        # Use auth service to validate credentials
        from src.auth.service import AuthService
        from src.database import async_session_factory

        async with async_session_factory() as session:
            service = AuthService(session)
            try:
                tokens = await service.login(str(email), str(password))
                # Verify user is admin
                from src.auth.jwt import decode_token
                payload = decode_token(tokens.access_token)
                if payload.get("role") != "admin":
                    return False
                request.session.update({
                    "token": tokens.access_token,
                    "user_id": payload["sub"],
                })
                await session.commit()
                return True
            except Exception:
                return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        try:
            from src.auth.jwt import decode_token
            payload = decode_token(token)
            return payload.get("role") == "admin"
        except Exception:
            return False
```

---

### Step 5.5 — Mount SQLAdmin in main.py

**Modify** `src/main.py`:

Add BEFORE the `return app` line:

```python
# SQLAdmin UI
from sqladmin import Admin
from starlette.middleware.sessions import SessionMiddleware

from src.admin.auth import AdminAuthBackend
from src.admin.views import (
    AnswerAdmin, CourseAdmin, EnrollmentAdmin, LessonAdmin,
    ProgressAdmin, QuestionAdmin, QuizAdmin, SubmissionAdmin, UserAdmin,
)

app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)

admin = Admin(
    app,
    engine,  # Use the sync or async engine from database.py
    authentication_backend=AdminAuthBackend(secret_key=settings.JWT_SECRET),
)
admin.add_view(UserAdmin)
admin.add_view(CourseAdmin)
admin.add_view(EnrollmentAdmin)
admin.add_view(LessonAdmin)
admin.add_view(QuizAdmin)
admin.add_view(QuestionAdmin)
admin.add_view(SubmissionAdmin)
admin.add_view(AnswerAdmin)
admin.add_view(ProgressAdmin)
```

Also mount the admin REST router:
```python
from src.admin.router import router as admin_router
app.include_router(admin_router, prefix="/api/v1")
```

> **IMPORTANT**: SQLAdmin needs the engine from `src.database`. Import it:
> `from src.database import engine`
>
> **POTENTIAL GOTCHA**: SQLAdmin may require a sync engine. If you get errors
> about async engine not being supported, create a separate sync engine in
> `database.py`:
> ```python
> from sqlalchemy import create_engine
> sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
> ```
> Then pass `sync_engine` to `Admin()`. Log this in gotchas.md if it happens.

**Update** `src/admin/__init__.py`:
```python
"""Admin module — REST CRUD endpoints and SQLAdmin UI for platform management."""
```

---

### Step 5.6 — Tests

**Create** `tests/admin/test_admin_router.py`:
- `test_admin_list_users_200` — admin can list all users
- `test_admin_get_user_200` — admin can get any user
- `test_admin_update_user_200` — admin can update any user
- `test_admin_delete_user_204` — admin can delete a user
- `test_admin_list_courses_200` — admin can list all courses
- `test_admin_delete_course_204`
- `test_admin_endpoints_403_student` — student gets 401 on all admin endpoints
- `test_admin_endpoints_403_instructor` — instructor gets 401 on all admin endpoints

**Create** `tests/admin/test_admin.py`:
- `test_health_check_still_works` — health endpoint still returns 200 after SQLAdmin mount
- `test_app_starts_with_sqladmin` — app creation doesn't crash

---

## Verification Commands

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests/admin/ -v --tb=short
uv run pytest tests/ --tb=short -q  # all tests still pass
# Manual: visit http://localhost:8001/admin — should show login page
# Manual: visit http://localhost:8001/docs — should show admin endpoints
```

## Error Tracking
If ANY mistake occurs → log in `gotchas.md`, update `.claude/CLAUDE.md`.

## Checkpoint
✅ Admin can CRUD all entities via REST API. SQLAdmin UI accessible at `/admin` with login.

## API Changelog Entry
```markdown
## v0.5.0 — Phase 5: Admin Features
- GET /api/v1/admin/users (Admin)
- GET /api/v1/admin/users/{id} (Admin)
- PATCH /api/v1/admin/users/{id} (Admin)
- DELETE /api/v1/admin/users/{id} (Admin)
- GET /api/v1/admin/courses (Admin)
- GET /api/v1/admin/courses/{id} (Admin)
- PATCH /api/v1/admin/courses/{id} (Admin)
- DELETE /api/v1/admin/courses/{id} (Admin)
- GET /api/v1/admin/submissions (Admin)
- DELETE /api/v1/admin/submissions/{id} (Admin)
- GET /api/v1/admin/progress (Admin)
- GET /admin — SQLAdmin UI (web interface)
```
