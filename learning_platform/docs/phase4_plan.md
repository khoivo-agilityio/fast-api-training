# Phase 4 — Progress Tracking

**Target Agent**: Claude Sonnet 4.6 (or equivalent)
**Prerequisites**: Phase 0, 1, 2, 3 completed. Quizzes + Submissions working.
**Branch**: `feat/implement-courses-lessons-enrollment`

---

## Context for Agent

### What Already Exists
- `src/progress/` — empty module with only `__init__.py`
- `tests/progress/` — empty with only `__init__.py`
- `src/config.py` — has `QUIZ_PASS_THRESHOLD: int = 70`
- Phase 3 left a `# TODO: Phase 4` comment in `submissions/service.py`

### How Progress Works (from `analysys_plan.md` Section 3)
- Progress is tracked **per (user, lesson)** — a single `progress` table
- **Course-level progress is DERIVED** — count completed lessons / total lessons
- Status transitions: `not_started` → `in_progress` → `completed`
- **Lesson has quiz** → `completed` when student scores ≥ `QUIZ_PASS_THRESHOLD` (70%)
- **Lesson has NO quiz** → `completed` when student visits (GET `/lessons/{id}`)
- There is NO stored course-level progress row — it's always computed

### Cross-Module Integration Points
1. `lessons/router.py` → `GET /lessons/{lesson_id}` must call `progress.service.touch()` for students
2. `submissions/service.py` → `submit()` must call `progress.service.mark_lesson_completed()` when score ≥ threshold

### Established Patterns (follow exactly)
See Phase 3 plan (`docs/phase3_plan.md`) for full pattern reference. Key points:
- Class-based service: `__init__(self, db: AsyncSession)`
- Domain exceptions from `<module>/exceptions.py`
- Thin routers, Pydantic schemas with `from_attributes = True`
- Test helpers in `tests/conftest.py`
- Explicit `updated_at` in service updates (gotchas #14)

---

## Execution Steps

### Step 4.1 — Progress ORM Model

**Create** `src/progress/models.py`:

```python
"""Progress ORM Model — tracks lesson-level completion per user."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ProgressStatus(StrEnum):
    """Lesson progress states."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Progress(Base):
    """Progress — tracks one user's progress on one lesson."""

    __tablename__ = "progress"
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ProgressStatus.NOT_STARTED.value
    )
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
```

**Update** `src/progress/__init__.py`:
```python
"""Progress module — Lesson-level progress tracking with course-level derivation."""
```

---

### Step 4.2 — Progress Schemas

**Create** `src/progress/schemas.py`:

```python
"""Progress Schemas (DTOs) — Pydantic v2."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LessonProgressResponse(BaseModel):
    """Single lesson progress record."""
    lesson_id: UUID
    status: str
    accessed_at: datetime
    completed_at: datetime | None
    model_config = {"from_attributes": True}


class CourseProgressResponse(BaseModel):
    """Derived course-level progress (computed, not stored)."""
    course_id: UUID
    course_title: str
    completed_lessons: int
    total_lessons: int
    percent_complete: float
    is_complete: bool
```

---

### Step 4.3 — Progress Exceptions

**Create** `src/progress/exceptions.py`:

```python
"""Progress module exceptions."""

from src.exceptions import NotFoundError


class ProgressNotFound(NotFoundError):
    def __init__(self):
        super().__init__(
            detail="Progress record not found",
            error_code="PROGRESS_NOT_FOUND",
        )
```

---

### Step 4.4 — Progress Service (Core Logic)

**Create** `src/progress/service.py`:

This is the most critical service in this phase. Methods:

#### `touch(user_id, lesson_id, has_quiz: bool)`
- SELECT existing progress for (user_id, lesson_id)
- If none exists:
  - If `has_quiz=True` → create with `status=in_progress`
  - If `has_quiz=False` → create with `status=completed`, set `completed_at=now()`
- If exists and `status=not_started`:
  - Same logic as above
- If exists and `status=in_progress` and `has_quiz=False`:
  - Transition to `completed`, set `completed_at=now()`
- If exists and `status=completed`:
  - Update `accessed_at` only (idempotent)
- Flush and return Progress

#### `mark_lesson_completed(user_id, lesson_id)`
- SELECT existing progress for (user_id, lesson_id)
- If none exists → create with `status=completed`, `completed_at=now()`
- If exists → set `status=completed`, `completed_at=now()`
- Flush

#### `get_lesson_progress(user_id, lesson_id)` → Progress | None
- Simple SELECT

#### `get_course_progress(user_id, course_id)` → CourseProgressResponse
- Get course via `courses.service.get_by_id(course_id)` (for title + 404 check)
- Count total lessons: `SELECT COUNT(*) FROM lessons WHERE course_id=X`
- Count completed: `SELECT COUNT(*) FROM progress WHERE user_id=U AND lesson_id IN (SELECT id FROM lessons WHERE course_id=X) AND status='completed'`
- Compute percent: `round(100 * completed / total, 2)` (0 if total=0)
- Return CourseProgressResponse

#### `get_all_courses_progress(user_id)` → list[CourseProgressResponse]
- Get all enrolled course IDs: `SELECT course_id FROM enrollments WHERE user_id=U`
- For each course, call `get_course_progress(user_id, course_id)`
- Return list

---

### Step 4.5 — Progress Dependencies & Router

**Create** `src/progress/dependencies.py` — standard `get_progress_service()` factory.

**Create** `src/progress/router.py`:

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| GET | `/courses/{course_id}/progress` | `get_current_user` | Student's own progress for one course |
| GET | `/progress` | `get_current_user` | Student's progress across all enrolled courses |

Both endpoints should check enrollment for students (or allow admin/instructor).

---

### Step 4.6 — Integration: Modify Lessons Router

**Modify** `src/lessons/router.py` — the `get_lesson` endpoint:

After fetching the lesson, if the user is a student, track progress:

```python
@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    """Get a single lesson by ID. Tracks progress for students."""
    lesson = await lesson_service.get_by_id(lesson_id)

    # Track progress for students
    if current_user.role == "student":
        from src.progress.service import ProgressService
        from src.quizzes.models import Quiz

        progress_service = ProgressService(db)
        # Check if lesson has a quiz
        result = await db.execute(
            select(Quiz).where(Quiz.lesson_id == lesson_id).limit(1)
        )
        has_quiz = result.scalar_one_or_none() is not None
        await progress_service.touch(current_user.id, lesson_id, has_quiz)

    return LessonResponse.model_validate(lesson)
```

Add needed imports: `from sqlalchemy import select`, `from src.database import get_db`, `from sqlalchemy.ext.asyncio import AsyncSession`.

---

### Step 4.7 — Integration: Modify Submissions Service

**Modify** `src/submissions/service.py` — in the `submit()` method, after computing score:

```python
# Mark lesson completed if score meets threshold
from src.config import settings
from src.progress.service import ProgressService

if score >= settings.QUIZ_PASS_THRESHOLD:
    progress_service = ProgressService(self._db)
    await progress_service.mark_lesson_completed(user_id, quiz.lesson_id)
```

Remove the `# TODO: Phase 4` comment.

---

### Step 4.8 — Wire Up

**Modify** `src/models.py`:
```python
from src.progress.models import Progress  # noqa: F401
```
(Uncomment the existing line)

**Modify** `src/main.py`:
```python
from src.progress.router import router as progress_router
app.include_router(progress_router, prefix="/api/v1")
```

---

### Step 4.9 — Test Fixtures

**Modify** `tests/conftest.py` — add:

```python
async def create_test_progress(
    session, user_id, lesson_id, status="in_progress"
):
    from src.progress.models import Progress
    progress = Progress(
        user_id=user_id, lesson_id=lesson_id, status=status
    )
    session.add(progress)
    await session.flush()
    return progress
```

---

### Step 4.10 — Tests

**Create** `tests/progress/test_progress_service.py`:
- `test_touch_creates_in_progress` — first visit to lesson with quiz → `in_progress`
- `test_touch_no_quiz_auto_completes` — first visit to lesson without quiz → `completed`
- `test_touch_idempotent` — second call doesn't regress completed → in_progress
- `test_mark_lesson_completed` — sets status + completed_at
- `test_mark_lesson_completed_creates_if_missing` — no prior record → creates completed
- `test_get_course_progress_partial` — 2/3 completed → 66.67%
- `test_get_course_progress_100` — all completed → `is_complete=True`
- `test_get_course_progress_empty` — 0 lessons → 0%, is_complete=True
- `test_get_all_courses_progress` — multiple courses

**Create** `tests/progress/test_progress_router.py`:
- `test_get_course_progress_200` — returns correct percentages
- `test_get_all_progress_200` — returns all enrolled courses
- `test_get_course_progress_401_no_auth`
- `test_get_course_progress_404_course`

**Update** `tests/lessons/test_lesson_router.py` — add:
- `test_get_lesson_tracks_progress_student` — GET lesson by student creates progress record

**Update** `tests/submissions/test_submission_service.py` — add:
- `test_submit_passing_score_marks_completed` — score ≥ 70 triggers mark_lesson_completed

---

## Verification Commands

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests/progress/ -v --tb=short
uv run pytest tests/ --tb=short -q  # all tests still pass
```

## Error Tracking
If ANY mistake occurs → log in `gotchas.md`, update `.claude/CLAUDE.md`.

## Checkpoint
✅ Student views lesson (no quiz) → auto-completed. Student passes quiz → lesson completed.
`GET /courses/{id}/progress` shows 66% (2/3). `GET /progress` shows all courses.

## API Changelog Entry
```markdown
## v0.4.0 — Phase 4: Progress Tracking
- GET /api/v1/courses/{course_id}/progress (Student — own progress)
- GET /api/v1/progress (Student — all enrolled courses)
- Lesson auto-completion on view (no-quiz lessons)
- Quiz pass (≥70%) triggers lesson completion
```
