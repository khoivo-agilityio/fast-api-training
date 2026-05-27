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
from sqlalchemy.orm import selectinload

from src.config import settings
from src.core.exceptions import ValidationError
from src.submissions.exceptions import AlreadySubmitted, SubmissionNotFound
from src.submissions.models import Answer, Submission
from src.submissions.repository import AnswerRepository, SubmissionRepository
from src.submissions.schemas import SubmissionDetailResponse, SubmitQuizRequest


class SubmissionService:
    """Handles quiz submission, grading, and retrieval."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self.submission_repo = SubmissionRepository(db)
        self.answer_repo = AnswerRepository(db)

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
        self,
        quiz_id: UUID,
        user_id: UUID,
        data: SubmitQuizRequest,
        *,
        quiz_service,
        lesson_service,
        course_service,
        progress_service,
    ) -> SubmissionDetailResponse:
        """Submit answers for a quiz. Auto-grades and returns results.

        Steps:
        1. Load quiz → lesson → check enrollment
        2. Check no prior submission (raise AlreadySubmitted)
        3. Load all questions
        4. Validate all questions are answered (no missing, no extra, no duplicates)
        5. Grade each answer
        6. Compute score, create Submission + Answer records
        7. Trigger progress completion if score >= threshold
        """
        # 1. Load quiz, lesson, check enrollment
        quiz = await quiz_service.get_quiz_by_id(quiz_id)
        lesson = await lesson_service.get_by_id(quiz.lesson_id)
        await course_service.check_enrollment(user_id, lesson.course_id)

        # 2. Check no prior submission
        existing = await self.submission_repo.get_by_user_and_quiz(user_id, quiz_id)
        if existing:
            raise AlreadySubmitted()

        # 3. Load all questions
        _, questions = await quiz_service.get_quiz_with_questions(quiz_id)

        # Build question lookup
        question_map = {q.id: q for q in questions}

        # 4. Validate answers — no missing, no extra, no duplicates
        submitted_ids = [a.question_id for a in data.answers]
        submitted_id_set = set(submitted_ids)
        all_question_ids = set(question_map.keys())

        # Check for duplicate question IDs in submission
        if len(submitted_ids) != len(submitted_id_set):
            raise ValidationError(
                detail="Duplicate answers detected — each question must be answered exactly once",
                error_code="DUPLICATE_ANSWERS",
            )

        # Check for answers referencing questions not in this quiz
        unknown_ids = submitted_id_set - all_question_ids
        if unknown_ids:
            raise ValidationError(
                detail=f"Answers reference {len(unknown_ids)} question(s) not in this quiz",
                error_code="UNKNOWN_QUESTIONS",
            )

        # Check for unanswered questions
        unanswered = all_question_ids - submitted_id_set
        if unanswered:
            raise ValidationError(
                detail=f"Missing answers for {len(unanswered)} question(s)",
                error_code="MISSING_ANSWERS",
            )

        # 5. Grade each answer
        answer_objects: list[Answer] = []
        correct_count = 0

        for answer_data in data.answers:
            question = question_map[answer_data.question_id]

            is_correct = self._grade_answer(question.correct_answer, answer_data.text)
            if is_correct:
                correct_count += 1

            answer_obj = Answer(
                question_id=answer_data.question_id,
                text=answer_data.text,
                is_correct=is_correct,
            )
            answer_objects.append(answer_obj)

        # 6. Compute score and create submission
        score = self._compute_score(correct_count, len(questions))
        submission = Submission(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
        )
        self.submission_repo.add(submission)
        await self._db.flush()

        # Link answers to submission
        for answer_obj in answer_objects:
            answer_obj.submission_id = submission.id
            self.answer_repo.add(answer_obj)
        await self._db.flush()

        # 7. Trigger progress completion if score >= threshold
        if score >= settings.QUIZ_PASS_THRESHOLD:
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
        submission = await self.submission_repo.get_by_user_and_quiz(user_id, quiz_id)
        if not submission:
            raise SubmissionNotFound()  # pragma: no cover
        return submission

    async def get_submission_with_answers(
        self, quiz_id: UUID, user_id: UUID
    ) -> SubmissionDetailResponse:
        """Get a user's submission with answers for a quiz."""
        submission = await self.submission_repo.get_with_answers(user_id, quiz_id)
        if not submission:
            raise SubmissionNotFound()

        answer_responses = [
            {
                "id": a.id,
                "question_id": a.question_id,
                "text": a.text,
                "is_correct": a.is_correct,
            }
            for a in submission.answers
        ]

        return SubmissionDetailResponse(  # pragma: no cover
            id=submission.id,
            quiz_id=submission.quiz_id,
            user_id=submission.user_id,
            score=submission.score,
            submitted_at=submission.submitted_at,
            answers=answer_responses,
        )

    # ── Admin helpers ──────────────────────────────────────────

    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Submission]:
        """List all submissions with pagination (admin use)."""
        return await self.submission_repo.list_all(limit, offset)

    async def get_by_id(self, submission_id: UUID) -> Submission | None:
        """Get a submission by ID (returns None if not found)."""
        return await self.submission_repo.get_by_id(submission_id)

    async def delete(self, submission_id: UUID) -> None:
        """Delete a submission by ID (admin use)."""
        submission = await self.get_by_id(submission_id)
        if submission:  # pragma: no cover
            await self.submission_repo.delete(submission)  # pragma: no cover
            await self._db.flush()  # pragma: no cover
