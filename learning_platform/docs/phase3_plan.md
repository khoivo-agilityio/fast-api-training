# Phase 3 — Quizzes, Submissions, Auto-Grading

**Target Agent**: Claude Sonnet 4.6 (or equivalent)
**Prerequisites**: Phase 0, 1, 2 completed. Courses + Lessons + Enrollment modules working.
**Branch**: `feat/implement-courses-lessons-enrollment`

---

## Context for Agent

### Project Architecture
- **Module-by-feature** layout under `src/` — each module owns its router, schemas, models, service, exceptions, dependencies
- **Class-based services**: `__init__(self, db: AsyncSession)`, wired via `Depends()` factory in `dependencies.py`
- **Thin routers**: no try/except, no DB queries — just parse → call service → return schema
- **Domain exceptions**: services raise from `<module>/exceptions.py`; global handler in `main.py` maps to HTTP status via MRO walk
- **Tests**: aiosqlite in-memory DB, mocked Redis, both service-level and router-level (httpx)

### Key Established Patterns (follow exactly)

**Service pattern** (see `src/courses/service.py`):
```python
class CourseService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
    async def create(self, data: ..., ...) -> OrmModel:
        ...
        self._db.add(obj)
        await self._db.flush()
        return obj
```

**Exception pattern** (see `src/courses/exceptions.py`):
```python
class CourseNotFound(NotFoundError):
    def __init__(self, course_id=None):
        detail = f"Course not found: {course_id}" if course_id else "Course not found"
        super().__init__(detail=detail, error_code="COURSE_NOT_FOUND")
```

**Router pattern** (see `src/courses/router.py`):
```python
@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    data: CourseCreateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    course = await service.create(data, current_user.id)
    return CourseResponse.model_validate(course)
```

**Test helper pattern** (see `tests/conftest.py`):
```python
async def create_test_course(session, instructor_id, title="Test Course", ...):
    from src.courses.models import Course
    course = Course(title=title, instructor_id=instructor_id, ...)
    session.add(course)
    await session.flush()
    return course
```

### Known Gotchas
- **#14**: `onupdate=func.now()` causes `MissingGreenlet` in aiosqlite — set `updated_at` explicitly in service update methods
- **#9**: aiosqlite doesn't support PG-specific features — use `Integer` instead of `Interval` for `time_limit`
- **#3**: Must import all models before `create_all` — `tests/conftest.py` imports `src.models`
- **#2**: Exception handler uses MRO walk — subclass exceptions automatically get correct HTTP status

### Reference Files
- ERD: `docs/erd.md`
- Analysis plan: `docs/analysys_plan.md` (sections 5-8 for schemas/services specs)
- Config: `src/config.py` — has `QUIZ_PASS_THRESHOLD: int = 70`

---

## Execution Steps

### Step 3.1 — Quiz & Question ORM Models

**Create** `src/quizzes/models.py`:

```python
"""Quiz & Question ORM Models."""

import uuid

from enum import StrEnum
from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class QuestionType(StrEnum):
    """Quiz question types."""
    MCQ = "mcq"
    TEXT = "text"


class Quiz(Base):
    """Quiz — belongs to a lesson. One quiz per lesson."""

    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Using Integer minutes instead of Interval — SQLite doesn't support Interval (gotchas #9)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Question(Base):
    """Question — belongs to a quiz. Supports MCQ and text types."""

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        String(10), nullable=False, default=QuestionType.MCQ.value
    )
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
```

**Update** `src/quizzes/__init__.py`:
```python
"""Quizzes module — Quiz & Question CRUD, linked to lessons."""
```

---

### Step 3.2 — Quiz Schemas

**Create** `src/quizzes/schemas.py`:

```python
"""Quiz & Question Schemas (DTOs) — Pydantic v2."""

from uuid import UUID

from pydantic import BaseModel, Field


class QuizCreateRequest(BaseModel):
    """Create quiz for a lesson."""
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    time_limit_minutes: int | None = Field(None, gt=0)


class QuizUpdateRequest(BaseModel):
    """Partial update quiz."""
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    time_limit_minutes: int | None = None


class QuestionCreateRequest(BaseModel):
    """Add a question to a quiz."""
    text: str = Field(min_length=1)
    type: str = Field(pattern="^(mcq|text)$")
    options: list[str] | None = None
    correct_answer: str = Field(min_length=1)


class QuestionUpdateRequest(BaseModel):
    """Partial update question."""
    text: str | None = None
    type: str | None = Field(None, pattern="^(mcq|text)$")
    options: list[str] | None = None
    correct_answer: str | None = None


class QuestionStudentResponse(BaseModel):
    """Question as seen by students — correct_answer hidden."""
    id: UUID
    quiz_id: UUID
    text: str
    type: str
    options: list[str] | None
    model_config = {"from_attributes": True}


class QuestionAdminResponse(QuestionStudentResponse):
    """Question as seen by instructors/admins — includes correct_answer."""
    correct_answer: str


class QuizResponse(BaseModel):
    """Quiz response without questions list."""
    id: UUID
    lesson_id: UUID
    title: str
    description: str | None
    time_limit_minutes: int | None
    question_count: int = 0
    model_config = {"from_attributes": True}


class QuizDetailResponse(BaseModel):
    """Quiz with questions list (student view)."""
    id: UUID
    lesson_id: UUID
    title: str
    description: str | None
    time_limit_minutes: int | None
    questions: list[QuestionStudentResponse]
    model_config = {"from_attributes": True}
```

---

### Step 3.3 — Quiz Exceptions

**Create** `src/quizzes/exceptions.py`:

```python
"""Quiz module exceptions."""

from src.exceptions import ConflictError, NotFoundError


class QuizNotFound(NotFoundError):
    def __init__(self, identifier: object = None):
        detail = f"Quiz not found: {identifier}" if identifier else "Quiz not found"
        super().__init__(detail=detail, error_code="QUIZ_NOT_FOUND")


class QuestionNotFound(NotFoundError):
    def __init__(self, identifier: object = None):
        detail = f"Question not found: {identifier}" if identifier else "Question not found"
        super().__init__(detail=detail, error_code="QUESTION_NOT_FOUND")


class QuizAlreadyExists(ConflictError):
    def __init__(self):
        super().__init__(
            detail="This lesson already has a quiz",
            error_code="QUIZ_ALREADY_EXISTS",
        )
```

---

### Step 3.4 — Quiz Service

**Create** `src/quizzes/service.py`:

Key methods:
- `create_quiz(lesson_id, data)` — check no existing quiz for this lesson first; raise `QuizAlreadyExists` if one exists
- `get_quiz_by_lesson(lesson_id)` → Quiz or raises `QuizNotFound`
- `get_quiz_by_id(quiz_id)` → Quiz or raises `QuizNotFound`
- `get_quiz_with_questions(quiz_id)` → (Quiz, list[Question]) — loads quiz + all questions; used by submissions service
- `update_quiz(lesson_id, data)` → Quiz
- `delete_quiz(lesson_id)` → None
- `add_question(quiz_id, data)` → Question
- `update_question(question_id, data)` → Question
- `delete_question(question_id)` → None
- `count_questions(quiz_id)` → int

Pattern: use `select(Quiz).where(Quiz.lesson_id == lesson_id)` for lesson-scoped lookups.
For `get_quiz_with_questions`: run two queries — get quiz, then `select(Question).where(Question.quiz_id == quiz_id)`.

---

### Step 3.5 — Quiz Dependencies & Router

**Create** `src/quizzes/dependencies.py` — standard `get_quiz_service()` factory.

**Create** `src/quizzes/router.py`:

Endpoints:
| Method | Path | Auth | Handler logic |
|--------|------|------|---------------|
| POST | `/lessons/{lesson_id}/quiz` | `require_roles("instructor", "admin")` | Verify instructor owns the lesson's course, then create quiz |
| GET | `/lessons/{lesson_id}/quiz` | `get_current_user` | Return `QuizDetailResponse` — student view hides `correct_answer` |
| PATCH | `/lessons/{lesson_id}/quiz` | `require_roles("instructor", "admin")` | Verify ownership, update quiz |
| DELETE | `/lessons/{lesson_id}/quiz` | `require_roles("instructor", "admin")` | Verify ownership, delete quiz |
| POST | `/quizzes/{quiz_id}/questions` | `require_roles("instructor", "admin")` | Verify ownership via quiz → lesson → course, add question |
| PATCH | `/questions/{question_id}` | `require_roles("instructor", "admin")` | Verify ownership, update question |
| DELETE | `/questions/{question_id}` | `require_roles("instructor", "admin")` | Verify ownership, delete question |

**Ownership check pattern** (reuse from lessons router):
```python
lesson = await lesson_service.get_by_id(lesson_id)
course = await course_service.get_by_id(lesson.course_id)
if current_user.role != "admin" and course.instructor_id != current_user.id:
    raise NotCourseOwner()
```

---

### Step 3.6 — Submission & Answer ORM Models

**Create** `src/submissions/models.py`:

```python
"""Submission & Answer ORM Models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class Submission(Base):
    """Student's quiz submission with auto-graded score."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Answer(Base):
    """Individual answer within a submission."""

    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
```

**Update** `src/submissions/__init__.py`:
```python
"""Submissions module — Quiz submission, auto-grading, and answer tracking."""
```

---

### Step 3.7 — Grading Logic (Pure Functions)

**Create** `src/submissions/grading.py`:

```python
"""Pure grading helpers — no DB, no side effects, no imports from other modules."""


def grade_answer(correct_answer: str, student_answer: str) -> bool:
    """Case-insensitive string equality for both MCQ and text questions."""
    return correct_answer.strip().lower() == student_answer.strip().lower()


def compute_score(correct_count: int, total_count: int) -> float:
    """Compute percentage score. Returns 0.0 if total is 0."""
    if total_count == 0:
        return 0.0
    return round(100.0 * correct_count / total_count, 2)
```

---

### Step 3.8 — Submission Schemas

**Create** `src/submissions/schemas.py`:

```python
"""Submission Schemas (DTOs) — Pydantic v2."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    """Single answer in a quiz submission."""
    question_id: UUID
    text: str = Field(min_length=1)


class SubmitQuizRequest(BaseModel):
    """Submit answers for a quiz."""
    answers: list[AnswerSubmission] = Field(min_length=1)


class AnswerResultResponse(BaseModel):
    """Single answer result after grading."""
    id: UUID
    question_id: UUID
    text: str
    is_correct: bool
    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    """Submission summary."""
    id: UUID
    quiz_id: UUID
    user_id: UUID
    score: float
    submitted_at: datetime
    model_config = {"from_attributes": True}


class SubmissionDetailResponse(SubmissionResponse):
    """Submission with individual answer results."""
    answers: list[AnswerResultResponse]
```

---

### Step 3.9 — Submission Exceptions

**Create** `src/submissions/exceptions.py`:

```python
"""Submission module exceptions."""

from src.exceptions import ConflictError, NotFoundError


class AlreadySubmitted(ConflictError):
    def __init__(self):
        super().__init__(
            detail="You have already submitted this quiz",
            error_code="ALREADY_SUBMITTED",
        )


class SubmissionNotFound(NotFoundError):
    def __init__(self, identifier: object = None):
        detail = f"Submission not found: {identifier}" if identifier else "Submission not found"
        super().__init__(detail=detail, error_code="SUBMISSION_NOT_FOUND")
```

---

### Step 3.10 — Submission Service

**Create** `src/submissions/service.py`:

The `submit()` method is the critical business logic:

```
1. Load the quiz via quizzes.service.get_quiz_by_id(quiz_id)
2. Load the lesson via lessons.service.get_by_id(quiz.lesson_id)
3. Check enrollment: courses.service.check_enrollment(user_id, lesson.course_id)
4. Check no prior submission: SELECT FROM submissions WHERE user_id=X AND quiz_id=Y
   → raise AlreadySubmitted if found
5. Load all questions: SELECT FROM questions WHERE quiz_id=Y
6. For each answer in request.answers:
   - Find the matching question
   - Grade: is_correct = grading.grade_answer(question.correct_answer, answer.text)
   - Create Answer ORM object
7. correct_count = sum(1 for a in answers if a.is_correct)
8. score = grading.compute_score(correct_count, len(questions))
9. Create Submission ORM with score
10. Add all Answer ORM objects
11. Flush
12. Return SubmissionDetailResponse
```

**Cross-module calls**: Instantiate other services within submit():
```python
from src.courses.service import CourseService
from src.lessons.service import LessonService
from src.quizzes.service import QuizService

course_service = CourseService(self._db)
lesson_service = LessonService(self._db)
quiz_service = QuizService(self._db)
```

**Note**: Progress integration (mark_lesson_completed when score ≥ threshold) will be added in Phase 4. For now, just do the grading and return the result. Add a `# TODO: Phase 4 — call progress.service.mark_lesson_completed` comment.

---

### Step 3.11 — Submission Dependencies & Router

**Create** `src/submissions/dependencies.py` — standard `get_submission_service()` factory.

**Create** `src/submissions/router.py`:

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/quizzes/{quiz_id}/submit` | `require_roles("student")` | Calls `service.submit()` |
| GET | `/quizzes/{quiz_id}/submission` | `get_current_user` | Returns own submission only |

---

### Step 3.12 — Wire Up

**Modify** `src/models.py` — uncomment quiz and submission re-exports:
```python
from src.quizzes.models import Question, Quiz  # noqa: F401
from src.submissions.models import Answer, Submission  # noqa: F401
```

**Modify** `src/main.py` — mount routers:
```python
from src.quizzes.router import router as quizzes_router
from src.submissions.router import router as submissions_router
app.include_router(quizzes_router, prefix="/api/v1")
app.include_router(submissions_router, prefix="/api/v1")
```

---

### Step 3.13 — Test Fixtures

**Modify** `tests/conftest.py` — add helpers:

```python
async def create_test_quiz(session, lesson_id, title="Test Quiz"):
    from src.quizzes.models import Quiz
    quiz = Quiz(lesson_id=lesson_id, title=title)
    session.add(quiz)
    await session.flush()
    return quiz


async def create_test_question(
    session, quiz_id, text="What is 2+2?",
    q_type="mcq", options=None, correct_answer="4"
):
    from src.quizzes.models import Question
    if options is None:
        options = ["1", "2", "3", "4"]
    question = Question(
        quiz_id=quiz_id, text=text, type=q_type,
        options=options, correct_answer=correct_answer,
    )
    session.add(question)
    await session.flush()
    return question
```

---

### Step 3.14 — Tests

**Create** `tests/quizzes/test_quiz_service.py`:
- `test_create_quiz` — instructor creates quiz for lesson
- `test_create_quiz_duplicate` → raises `QuizAlreadyExists`
- `test_get_quiz_by_lesson_found` / `test_get_quiz_by_lesson_not_found`
- `test_get_quiz_with_questions` — returns quiz + all questions
- `test_add_question` / `test_update_question` / `test_delete_question`
- `test_count_questions`

**Create** `tests/quizzes/test_quiz_router.py`:
- `test_create_quiz_201_instructor` / `test_create_quiz_409_duplicate`
- `test_get_quiz_200` / `test_get_quiz_404`
- `test_create_quiz_403_wrong_instructor`
- `test_add_question_201` / `test_delete_question_204`

**Create** `tests/submissions/test_grading.py`:
- `test_grade_answer_exact_match` → True
- `test_grade_answer_case_insensitive` → True
- `test_grade_answer_wrong` → False
- `test_grade_answer_whitespace_trimmed` → True
- `test_compute_score_all_correct` → 100.0
- `test_compute_score_partial` → correct percentage
- `test_compute_score_zero_total` → 0.0

**Create** `tests/submissions/test_submission_service.py`:
- `test_submit_all_correct` → score=100
- `test_submit_partial` → correct percentage
- `test_submit_duplicate` → raises `AlreadySubmitted`
- `test_submit_not_enrolled` → raises `NotEnrolled`

**Create** `tests/submissions/test_submission_router.py`:
- `test_submit_201` → returns score
- `test_submit_409_duplicate`
- `test_get_submission_200` → returns own submission
- `test_get_submission_404` → no submission yet

---

## Verification Commands

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run pytest tests/quizzes/ tests/submissions/ -v --tb=short
uv run pytest tests/ --tb=short -q  # all tests still pass
```

## Error Tracking
If ANY mistake occurs during implementation:
1. Log it in `gotchas.md` (project root)
2. Update `.claude/CLAUDE.md` with the corrected rule
3. Update `.github/copilot-instructions.md` if it exists

## Checkpoint
✅ Instructor creates quiz with questions → Student submits → Auto-graded → Score returned → `GET /submission` shows results.

## API Changelog Entry (append to `docs/api/CHANGELOG.md`)
```markdown
## v0.3.0 — Phase 3: Quizzes, Submissions, Auto-Grading
- POST /api/v1/lessons/{lesson_id}/quiz (Instructor/Admin)
- GET /api/v1/lessons/{lesson_id}/quiz (Any authenticated)
- PATCH /api/v1/lessons/{lesson_id}/quiz (Instructor/Admin)
- DELETE /api/v1/lessons/{lesson_id}/quiz (Instructor/Admin)
- POST /api/v1/quizzes/{quiz_id}/questions (Instructor/Admin)
- PATCH /api/v1/questions/{id} (Instructor/Admin)
- DELETE /api/v1/questions/{id} (Instructor/Admin)
- POST /api/v1/quizzes/{quiz_id}/submit (Student, enrolled)
- GET /api/v1/quizzes/{quiz_id}/submission (Own submission)
```
