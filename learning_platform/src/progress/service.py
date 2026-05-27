"""
Progress Service — Lesson-level progress tracking with course-level derivation.

Class-based service pattern:
- Takes AsyncSession via constructor
- All DB queries are owned by this service via ProgressRepository
- Cross-domain data is accessed through injected CourseService / LessonService
- Raises domain exceptions — never HTTPException

Key behaviours:
- touch()              : Called by LessonService.get_and_track() for students
- mark_lesson_completed: Called by submissions service when quiz score >= threshold
- get_course_progress  : Derives progress from the progress table (no stored aggregate)
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.lessons.service import LessonService
from src.progress.models import Progress, ProgressStatus
from src.progress.repository import ProgressRepository
from src.progress.schemas import CourseProgressResponse


class ProgressService:
    """Handles lesson progress tracking and course-level progress derivation."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self.repo = ProgressRepository(db)

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
        progress = await self.repo.get_by_user_and_lesson(user_id, lesson_id)
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
            self.repo.add(progress)
        elif progress.status == ProgressStatus.NOT_STARTED:
            # Transition from not_started
            if has_quiz:  # pragma: no cover
                progress.status = ProgressStatus.IN_PROGRESS  # pragma: no cover
            else:  # pragma: no cover
                progress.status = ProgressStatus.COMPLETED  # pragma: no cover
                progress.completed_at = now  # pragma: no cover
            progress.accessed_at = now  # pragma: no cover
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
        """Mark a lesson as completed (called after passing quiz)."""
        progress = await self.repo.get_by_user_and_lesson(user_id, lesson_id)
        now = datetime.now(UTC)

        if progress is None:
            progress = Progress(
                user_id=user_id,
                lesson_id=lesson_id,
                status=ProgressStatus.COMPLETED,
                accessed_at=now,
                completed_at=now,
            )
            self.repo.add(progress)
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
        return await self.repo.get_by_user_and_lesson(user_id, lesson_id)

    async def get_course_progress(
        self,
        user_id: UUID,
        course_id: UUID,
        course_service,
    ) -> CourseProgressResponse:
        """Derive course-level progress from lesson-level records.

        - course_service: CourseService — fetches course title and enrolled lesson IDs
        LessonService is created internally from the session.
        """
        # Raises CourseNotFound if the course doesn't exist
        course = await course_service.get_by_id(course_id)

        # Get all lesson IDs in this course via LessonService
        lesson_service = LessonService(self._db)
        lessons = await lesson_service.list_by_course(course_id)
        total = len(lessons)
        lesson_ids = [lesson.id for lesson in lessons]

        # Count how many of those lessons the user has completed
        completed = await self.repo.count_completed_in_lessons(user_id, lesson_ids)

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
        self,
        user_id: UUID,
        course_service,
    ) -> list[CourseProgressResponse]:
        """Return progress for all courses the user is enrolled in."""
        course_ids = await course_service.get_enrolled_course_ids(user_id)
        return [
            await self.get_course_progress(user_id, course_id, course_service)
            for course_id in course_ids
        ]

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Progress]:
        """List all progress records with pagination (admin use)."""
        return await self.repo.list_all(limit, offset)
