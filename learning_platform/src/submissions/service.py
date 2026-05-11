"""
Submission Service — Quiz submission and auto-grading.

Class-based service pattern:
- Takes AsyncSession via constructor
- Orchestrates cross-module calls for enrollment check and grading
- Raises domain exceptions — never HTTPException
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.submissions.exceptions import AlreadySubmitted, SubmissionNotFound
from src.submissions.models import Answer, Submission
from src.submissions.schemas import SubmissionDetailResponse, SubmitQuizRequest


class SubmissionService:
    """Handles quiz submission, grading, and retrieval."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _grade_answer(correct_answer: str, student_answer: str) -> bool:
        """Case-insensitive string equality for both MCQ and text questions."""
        return correct_answer.strip().lower() == student_answer.strip().lower()

    @staticmethod
    def _compute_score(correct_count: int, total_count: int) -> float:
        """Compute percentage score. Returns 0.0 if total is 0."""
        if total_count == 0:
            return 0.0
        return round(100.0 * correct_count / total_count, 2)

    async def submit(
        self, quiz_id: UUID, user_id: UUID, data: SubmitQuizRequest
    ) -> SubmissionDetailResponse:
        """Submit answers for a quiz. Auto-grades and returns results.

        Steps:
        1. Load quiz → lesson → check enrollment
        2. Check no prior submission (raise AlreadySubmitted)
        3. Load all questions
        4. Grade each answer
        5. Compute score, create Submission + Answer records
        6. Trigger progress completion if score >= threshold
        """
        from src.courses.service import CourseService
        from src.lessons.service import LessonService
        from src.quizzes.service import QuizService

        quiz_service = QuizService(self._db)
        lesson_service = LessonService(self._db)
        course_service = CourseService(self._db)

        # 1. Load quiz, lesson, check enrollment
        quiz = await quiz_service.get_quiz_by_id(quiz_id)
        lesson = await lesson_service.get_by_id(quiz.lesson_id)
        await course_service.check_enrollment(user_id, lesson.course_id)

        # 2. Check no prior submission
        result = await self._db.execute(
            select(Submission).where(Submission.user_id == user_id, Submission.quiz_id == quiz_id)
        )
        if result.scalar_one_or_none():
            raise AlreadySubmitted()

        # 3. Load all questions
        _, questions = await quiz_service.get_quiz_with_questions(quiz_id)

        # Build question lookup
        question_map = {q.id: q for q in questions}

        # 4. Grade each answer
        answer_objects: list[Answer] = []
        correct_count = 0

        for answer_data in data.answers:
            question = question_map.get(answer_data.question_id)
            if question is None:
                continue  # skip answers for unknown questions

            is_correct = self._grade_answer(question.correct_answer, answer_data.text)
            if is_correct:
                correct_count += 1

            answer_obj = Answer(
                question_id=answer_data.question_id,
                text=answer_data.text,
                is_correct=is_correct,
            )
            answer_objects.append(answer_obj)

        # 5. Compute score and create submission
        score = self._compute_score(correct_count, len(questions))
        submission = Submission(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
        )
        self._db.add(submission)
        await self._db.flush()

        # Link answers to submission
        for answer_obj in answer_objects:
            answer_obj.submission_id = submission.id
            self._db.add(answer_obj)
        await self._db.flush()

        # 6. Trigger progress completion if score >= threshold
        from src.config import settings
        from src.progress.service import ProgressService

        if score >= settings.QUIZ_PASS_THRESHOLD:
            progress_service = ProgressService(self._db)
            await progress_service.mark_lesson_completed(user_id, quiz.lesson_id)

        # Build response
        answer_responses = [
            {
                "id": a.id,
                "question_id": a.question_id,
                "text": a.text,
                "is_correct": a.is_correct,
            }
            for a in answer_objects
        ]

        return SubmissionDetailResponse(
            id=submission.id,
            quiz_id=submission.quiz_id,
            user_id=submission.user_id,
            score=submission.score,
            submitted_at=submission.submitted_at,
            answers=answer_responses,
        )

    async def get_user_submission(self, quiz_id: UUID, user_id: UUID) -> Submission:
        """Get a user's submission for a quiz, or raise SubmissionNotFound."""
        result = await self._db.execute(
            select(Submission).where(Submission.user_id == user_id, Submission.quiz_id == quiz_id)
        )
        submission = result.scalar_one_or_none()
        if not submission:
            raise SubmissionNotFound()
        return submission

    async def get_submission_with_answers(
        self, quiz_id: UUID, user_id: UUID
    ) -> SubmissionDetailResponse:
        """Get a user's submission with answers for a quiz."""
        submission = await self.get_user_submission(quiz_id, user_id)

        result = await self._db.execute(
            select(Answer).where(Answer.submission_id == submission.id)
        )
        answers = list(result.scalars().all())

        answer_responses = [
            {
                "id": a.id,
                "question_id": a.question_id,
                "text": a.text,
                "is_correct": a.is_correct,
            }
            for a in answers
        ]

        return SubmissionDetailResponse(
            id=submission.id,
            quiz_id=submission.quiz_id,
            user_id=submission.user_id,
            score=submission.score,
            submitted_at=submission.submitted_at,
            answers=answer_responses,
        )

    # ── Admin helpers (kept from original) ──────────────────────

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Submission]:
        """List all submissions with pagination (admin use)."""
        result = await self._db.execute(
            select(Submission).order_by(Submission.submitted_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_id(self, submission_id: UUID) -> Submission | None:
        """Get a submission by ID (returns None if not found)."""
        result = await self._db.execute(select(Submission).where(Submission.id == submission_id))
        return result.scalar_one_or_none()

    async def delete(self, submission_id: UUID) -> None:
        """Delete a submission by ID (admin use)."""
        submission = await self.get_by_id(submission_id)
        if submission:
            await self._db.delete(submission)
            await self._db.flush()
