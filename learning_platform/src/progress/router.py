"""
Progress Router — /api/v1/courses/{course_id}/progress + /api/v1/progress.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.

Endpoints:
  GET /courses/{course_id}/progress  — Student's own progress for one course
  GET /progress                      — Student's progress across all enrolled courses
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user, require_roles
from src.courses.dependencies import get_course_service
from src.courses.service import CourseService
from src.lessons.dependencies import get_lesson_service
from src.lessons.service import LessonService
from src.progress.dependencies import get_progress_service
from src.progress.schemas import CourseProgressResponse
from src.progress.service import ProgressService
from src.users.models import User

router = APIRouter(tags=["progress"])


@router.get("/courses/{course_id}/progress", response_model=CourseProgressResponse)
async def get_course_progress(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service),
    course_service: CourseService = Depends(get_course_service),
    lesson_service: LessonService = Depends(get_lesson_service),
) -> CourseProgressResponse:
    """Get the current user's progress for a single course.

    Admins and instructors can view without enrollment check.
    Students must be enrolled in the course (403 if not enrolled, 404 if course missing).
    """
    # For students, enforce enrollment — check course existence first for correct 404/403 order
    if current_user.role == "student":
        # Raises CourseNotFound (→ 404) if the course doesn't exist
        await course_service.get_by_id(course_id)
        # Raises NotEnrolled (→ 403) if the student isn't enrolled
        await course_service.check_enrollment(current_user.id, course_id)

    return await progress_service.get_course_progress(
        current_user.id, course_id, course_service, lesson_service
    )


@router.get("/progress", response_model=list[CourseProgressResponse])
async def get_all_progress(
    current_user: User = Depends(get_current_user),
    progress_service: ProgressService = Depends(get_progress_service),
    course_service: CourseService = Depends(get_course_service),
    lesson_service: LessonService = Depends(get_lesson_service),
) -> list[CourseProgressResponse]:
    """Get the current user's progress across all enrolled courses."""
    return await progress_service.get_all_courses_progress(
        current_user.id, course_service, lesson_service
    )


# ---------------------------------------------------------------------------
# Admin-only endpoints — /api/v1/admin/progress/*
# ---------------------------------------------------------------------------

admin_router = APIRouter(prefix="/admin/progress", tags=["admin"])


@admin_router.get("", response_model=list[dict])
async def admin_list_progress(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_roles("admin")),
    progress_service: ProgressService = Depends(get_progress_service),
) -> list[dict]:
    """List all progress records (admin only)."""
    records = await progress_service.list_all(limit=limit, offset=offset)
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "lesson_id": str(r.lesson_id),
            "status": r.status,
            "accessed_at": r.accessed_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in records
    ]
