"""
Course Service — Course CRUD + Enrollment.

Class-based service pattern:
- Takes AsyncSession via constructor
- All DB queries are owned by this service (no repositories layer)
- Raises domain exceptions — never HTTPException
- Cross-module access goes through service public methods only
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.courses.exceptions import (
    AlreadyEnrolled,
    CourseNotFound,
    NotCourseOwner,
    NotEnrolled,
)
from src.courses.models import Course, Enrollment
from src.courses.repository import CourseRepository, EnrollmentRepository
from src.courses.schemas import CourseCreateRequest, CourseUpdateRequest


class CourseService:
    """Handles course CRUD and enrollment operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self.course_repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    async def create(self, data: CourseCreateRequest, instructor_id: UUID) -> Course:
        """Create a new course owned by the given instructor."""
        course = Course(
            title=data.title,
            description=data.description,
            instructor_id=instructor_id,
        )
        self.course_repo.add(course)
        await self._db.flush()
        return course

    async def get_by_id(self, course_id: UUID) -> Course:
        """Get course by ID or raise CourseNotFound."""
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise CourseNotFound(course_id)
        return course

    async def list_courses(
        self,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
        instructor_id: UUID | None = None,
    ) -> tuple[list[Course], int]:
        """List courses with optional search and instructor filter. Returns (items, total)."""
        return await self.course_repo.list_courses(limit, offset, search, instructor_id)

    async def update(
        self, course_id: UUID, data: CourseUpdateRequest, user_id: UUID, user_role: str
    ) -> Course:
        """Update a course. Instructor can only update own courses; admin can update any."""
        course = await self.get_by_id(course_id)
        if user_role != "admin" and course.instructor_id != user_id:
            raise NotCourseOwner()

        update_data = data.model_dump(exclude_unset=True)
        update_data.pop("id", None)
        for field, value in update_data.items():
            setattr(course, field, value)

        course.updated_at = datetime.now(UTC)
        await self._db.flush()
        return course

    async def delete(self, course_id: UUID) -> None:
        """Delete a course (admin only — enforced at router level)."""
        course = await self.get_by_id(course_id)
        await self.course_repo.delete(course)
        await self._db.flush()

    async def enroll(self, user_id: UUID, course_id: UUID) -> Enrollment:
        """Enroll a student in a course. Raises AlreadyEnrolled if duplicate."""
        await self.get_by_id(course_id)  # Ensure course exists

        existing = await self.enrollment_repo.get_enrollment(user_id, course_id)
        if existing:
            raise AlreadyEnrolled()

        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        self.enrollment_repo.add(enrollment)
        await self._db.flush()
        return enrollment

    async def is_enrolled(self, user_id: UUID, course_id: UUID) -> bool:
        """Check if a user is enrolled in a course."""
        existing = await self.enrollment_repo.get_enrollment(user_id, course_id)
        return existing is not None

    async def check_enrollment(self, user_id: UUID, course_id: UUID) -> None:
        """Raise NotEnrolled if the user is not enrolled in the course."""
        if not await self.is_enrolled(user_id, course_id):
            raise NotEnrolled()

    async def get_enrolled_course_ids(self, user_id: UUID) -> list[UUID]:
        """Return all course IDs the user is enrolled in."""
        return await self.enrollment_repo.get_enrolled_course_ids(user_id)
