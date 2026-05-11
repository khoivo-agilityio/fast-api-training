"""
Lesson Router — /api/v1/courses/{course_id}/lessons + /api/v1/lessons/{id}.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_roles
from src.courses.dependencies import get_course_service
from src.courses.exceptions import NotCourseOwner
from src.courses.service import CourseService
from src.database import get_db
from src.lessons.dependencies import get_lesson_service
from src.lessons.schemas import LessonCreateRequest, LessonResponse, LessonUpdateRequest
from src.lessons.service import LessonService
from src.users.models import User

router = APIRouter(tags=["lessons"])


@router.post("/courses/{course_id}/lessons", response_model=LessonResponse, status_code=201)
async def create_lesson(
    course_id: UUID,
    data: LessonCreateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    course_service: CourseService = Depends(get_course_service),
    lesson_service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    """Create a new lesson in a course (owner instructor or admin)."""
    course = await course_service.get_by_id(course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    lesson = await lesson_service.create(course_id, data)
    return LessonResponse.model_validate(lesson)


@router.get("/courses/{course_id}/lessons", response_model=list[LessonResponse])
async def list_lessons(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service),
    lesson_service: LessonService = Depends(get_lesson_service),
) -> list[LessonResponse]:
    """List all lessons in a course, ordered by display order."""
    await course_service.get_by_id(course_id)  # 404 if course not found
    lessons = await lesson_service.list_by_course(course_id)
    return [LessonResponse.model_validate(lesson) for lesson in lessons]


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
        result = await db.execute(select(Quiz).where(Quiz.lesson_id == lesson_id).limit(1))
        has_quiz = result.scalar_one_or_none() is not None
        await progress_service.touch(current_user.id, lesson_id, has_quiz)

    return LessonResponse.model_validate(lesson)


@router.patch("/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: UUID,
    data: LessonUpdateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    course_service: CourseService = Depends(get_course_service),
    lesson_service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    """Update a lesson (owner instructor or admin)."""
    lesson = await lesson_service.get_by_id(lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    updated = await lesson_service.update(lesson_id, data)
    return LessonResponse.model_validate(updated)


@router.delete("/lessons/{lesson_id}", status_code=204)
async def delete_lesson(
    lesson_id: UUID,
    current_user: User = Depends(require_roles("instructor", "admin")),
    course_service: CourseService = Depends(get_course_service),
    lesson_service: LessonService = Depends(get_lesson_service),
) -> None:
    """Delete a lesson (owner instructor or admin)."""
    lesson = await lesson_service.get_by_id(lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    await lesson_service.delete(lesson_id)


# ---------------------------------------------------------------------------
# UI helper — /api/v1/admin/ui/lessons (used by SQLAdmin quiz create cascade)
# ---------------------------------------------------------------------------

ui_router = APIRouter(prefix="/admin/ui", tags=["admin"])


@ui_router.get("/lessons", include_in_schema=False)
async def admin_ui_lessons(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return lessons for a course as {id, title} for the cascading dropdown.

    No JWT auth — called via browser fetch from SQLAdmin which already enforces
    session-based admin authentication.
    """
    from sqlalchemy import select

    from src.lessons.models import Lesson

    result = await db.execute(
        select(Lesson.id, Lesson.title).where(Lesson.course_id == course_id).order_by(Lesson.order)
    )
    return [{"id": str(row.id), "title": row.title} for row in result.all()]
