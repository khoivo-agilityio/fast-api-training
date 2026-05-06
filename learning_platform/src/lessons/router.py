"""
Lesson Router — /api/v1/courses/{course_id}/lessons + /api/v1/lessons/{id}.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user, require_roles
from src.courses.dependencies import get_course_service
from src.courses.exceptions import NotCourseOwner
from src.courses.service import CourseService
from src.lessons.dependencies import get_lesson_service
from src.lessons.schemas import LessonCreateRequest, LessonResponse, LessonUpdateRequest
from src.lessons.service import LessonService
from src.users.models import User

router = APIRouter(tags=["lessons"])


@router.post(
    "/courses/{course_id}/lessons", response_model=LessonResponse, status_code=201
)
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
) -> LessonResponse:
    """Get a single lesson by ID."""
    lesson = await lesson_service.get_by_id(lesson_id)
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
