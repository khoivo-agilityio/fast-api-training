"""
Progress Service — Lesson-level progress tracking with course-level derivation.

Class-based service pattern:
- Takes AsyncSession via constructor
- All DB queries are owned by this service (no repositories layer)
- Raises domain exceptions — never HTTPException
- Cross-module access goes through service public methods only

Key behaviours:
- touch()              : Called by LessonService.get_and_track() for students
- mark_lesson_completed: Called by submissions service when quiz score >= threshold
- get_course_progress  : Derives progress from the progress table (no stored aggregate)
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.courses.models import Enrollment
from src.lessons.models import Lesson
from src.progress.models import Progress, ProgressStatus
from src.progress.schemas import CourseProgressResponse


class ProgressService:
    """Handles lesson progress tracking and course-level progress derivation."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Core tracking methods
    # ------------------------------------------------------------------

    async def touch(self, user_id: UUID, lesson_id: UUID, has_quiz: bool) -> Progress:
        """Record or update progress when a student views a lesson.

        Status transitions:
        - No record          → in_progress (has quiz) | completed (no quiz)
        - not_started        → in_progress (has quiz) | completed (no quiz)
        - in_progress + no quiz → completed
        - completed          → update accessed_at only (idempotent)
        """
        result = await self._db.execute(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.lesson_id == lesson_id,
            )
        )
        progress = result.scalar_one_or_none()
        now = datetime.now(UTC)

        if progress is None:
            # First visit — create record
            if has_quiz:
                progress = Progress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    status=ProgressStatus.IN_PROGRESS,
                    accessed_at=now,
                )
            else:
                progress = Progress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    status=ProgressStatus.COMPLETED,
                    accessed_at=now,
                    completed_at=now,
                )
            self._db.add(progress)
        elif progress.status == ProgressStatus.NOT_STARTED:
            # Transition from not_started
            if has_quiz:
                progress.status = ProgressStatus.IN_PROGRESS
            else:
                progress.status = ProgressStatus.COMPLETED
                progress.completed_at = now
            progress.accessed_at = now
        elif progress.status == ProgressStatus.IN_PROGRESS and not has_quiz:
            # Lesson has no quiz — auto-complete on revisit
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = now
            progress.accessed_at = now
        else:
            # Already completed — update accessed_at only (idempotent)
            progress.accessed_at = now

        await self._db.flush()
        return progress

    async def mark_lesson_completed(self, user_id: UUID, lesson_id: UUID) -> Progress:
        """Mark a lesson as completed (called after passing quiz).

        Creates a new record if none exists.
        """
        result = await self._db.execute(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.lesson_id == lesson_id,
            )
        )
        progress = result.scalar_one_or_none()
        now = datetime.now(UTC)

        if progress is None:
            progress = Progress(
                user_id=user_id,
                lesson_id=lesson_id,
                status=ProgressStatus.COMPLETED,
                accessed_at=now,
                completed_at=now,
            )
            self._db.add(progress)
        else:
            progress.status = ProgressStatus.COMPLETED
            progress.completed_at = now
            progress.accessed_at = now

        await self._db.flush()
        return progress

    # ------------------------------------------------------------------
    # Read methods
    # ------------------------------------------------------------------

    async def get_lesson_progress(self, user_id: UUID, lesson_id: UUID) -> Progress | None:
        """Return the progress record for (user, lesson) or None if it doesn't exist."""
        result = await self._db.execute(
            select(Progress).where(
                Progress.user_id == user_id,
                Progress.lesson_id == lesson_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_course_progress(
        self, user_id: UUID, course_id: UUID, course_service
    ) -> CourseProgressResponse:
        """Derive course-level progress from lesson-level records.

        Counts total lessons in the course and completed ones by the user.
        CourseService is injected as a parameter to avoid internal service creation.
        """
        # Raises CourseNotFound if the course doesn't exist
        course = await course_service.get_by_id(course_id)

        # Total lessons in course
        total_result = await self._db.execute(
            select(func.count()).select_from(Lesson).where(Lesson.course_id == course_id)
        )
        total = total_result.scalar_one()

        # Completed lessons by this user for this course
        completed_result = await self._db.execute(
            select(func.count())
            .select_from(Progress)
            .where(
                Progress.user_id == user_id,
                Progress.status == ProgressStatus.COMPLETED,
                Progress.lesson_id.in_(select(Lesson.id).where(Lesson.course_id == course_id)),
            )
        )
        completed = completed_result.scalar_one()

        percent = round(100 * completed / total, 2) if total > 0 else 0.0

        return CourseProgressResponse(
            course_id=course_id,
            course_title=course.title,
            completed_lessons=completed,
            total_lessons=total,
            percent_complete=percent,
            is_complete=(total > 0 and completed >= total),
        )

    async def get_all_courses_progress(
        self, user_id: UUID, course_service
    ) -> list[CourseProgressResponse]:
        """Return progress for all courses the user is enrolled in."""
        result = await self._db.execute(
            select(Enrollment.course_id).where(Enrollment.user_id == user_id)
        )
        course_ids = list(result.scalars().all())
        return [
            await self.get_course_progress(user_id, course_id, course_service)
            for course_id in course_ids
        ]

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Progress]:
        """List all progress records with pagination (admin use)."""
        result = await self._db.execute(
            select(Progress).order_by(Progress.accessed_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
