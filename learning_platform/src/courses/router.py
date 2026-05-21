"""
Course Router — /api/v1/courses endpoints.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.auth.admin_auth import require_admin_or_session
from src.auth.dependencies import get_current_user, require_roles
from src.core.pagination import PaginationParams
from src.courses.dependencies import get_course_service
from src.courses.schemas import (
    CourseCreateRequest,
    CourseListResponse,
    CourseResponse,
    CourseUpdateRequest,
    EnrollmentResponse,
)
from src.courses.service import CourseService
from src.users.models import User

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseResponse, status_code=201)
async def create_course(
    data: CourseCreateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    """Create a new course (instructor or admin only)."""
    course = await service.create(data, current_user.id)
    return CourseResponse.model_validate(course)


@router.get("", response_model=CourseListResponse)
async def list_courses(
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
    pagination: PaginationParams = Depends(),
    search: str | None = Query(None, description="Filter by title (case-insensitive)"),
    instructor: UUID | None = Query(None, description="Filter by instructor user ID"),
) -> CourseListResponse:
    """List courses with optional search and instructor filter (paginated)."""
    items, total = await service.list_courses(
        pagination.limit, pagination.offset, search, instructor
    )
    return CourseListResponse(
        items=[CourseResponse.model_validate(c) for c in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    """Get a course by ID."""
    course = await service.get_by_id(course_id)
    return CourseResponse.model_validate(course)


@router.patch("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: UUID,
    data: CourseUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    """Update a course (owner instructor or admin)."""
    course = await service.update(course_id, data, current_user.id, current_user.role)
    return CourseResponse.model_validate(course)


@router.delete("/{course_id}", status_code=204)
async def delete_course(
    course_id: UUID,
    current_user: User = Depends(require_roles("admin")),
    service: CourseService = Depends(get_course_service),
) -> None:
    """Delete a course (admin only)."""
    await service.delete(course_id)


@router.post("/{course_id}/enroll", response_model=EnrollmentResponse, status_code=201)
async def enroll_in_course(
    course_id: UUID,
    current_user: User = Depends(require_roles("student")),
    service: CourseService = Depends(get_course_service),
) -> EnrollmentResponse:
    """Enroll the current student in a course."""
    enrollment = await service.enroll(current_user.id, course_id)
    return EnrollmentResponse.model_validate(enrollment)


# ---------------------------------------------------------------------------
# Admin-only endpoints — /api/v1/admin/courses/*
# ---------------------------------------------------------------------------

admin_router = APIRouter(prefix="/admin/courses", tags=["admin"])


@admin_router.get("", response_model=list[CourseResponse])
async def admin_list_courses(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: None = Depends(require_roles("admin")),
    service: CourseService = Depends(get_course_service),
) -> list[CourseResponse]:
    """List all courses with pagination (admin only)."""
    courses, _ = await service.list_courses(limit=limit, offset=offset)
    return [CourseResponse.model_validate(c) for c in courses]


@admin_router.get("/{course_id}", response_model=CourseResponse)
async def admin_get_course(
    course_id: UUID,
    _: None = Depends(require_roles("admin")),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    """Get any course by ID (admin only)."""
    course = await service.get_by_id(course_id)
    return CourseResponse.model_validate(course)


@admin_router.patch("/{course_id}", response_model=CourseResponse)
async def admin_update_course(
    course_id: UUID,
    data: CourseUpdateRequest,
    _: None = Depends(require_roles("admin")),
    service: CourseService = Depends(get_course_service),
) -> CourseResponse:
    """Update any course (admin only — skips ownership check)."""
    from uuid import uuid4

    course = await service.update(course_id, data, user_id=uuid4(), user_role="admin")
    return CourseResponse.model_validate(course)


@admin_router.delete("/{course_id}", status_code=204)
async def admin_delete_course(
    course_id: UUID,
    _: None = Depends(require_roles("admin")),
    service: CourseService = Depends(get_course_service),
) -> None:
    """Delete any course (admin only)."""
    await service.delete(course_id)


# ---------------------------------------------------------------------------
# UI helper — /api/v1/admin/ui/courses (used by SQLAdmin quiz create cascade)
# ---------------------------------------------------------------------------

ui_router = APIRouter(prefix="/admin/ui", tags=["admin"])


@ui_router.get("/courses", include_in_schema=False)
async def admin_ui_courses(
    _: None = Depends(require_admin_or_session),
    service: CourseService = Depends(get_course_service),
) -> list[dict]:
    """Return all courses as {id, title} for the cascading dropdown in Quiz create.

    Protected by dual auth — accepts JWT Bearer (admin) or SQLAdmin session cookie.
    """
    courses, _ = await service.list_courses(limit=500, offset=0)
    return [{"id": str(c.id), "title": c.title} for c in courses]
