"""
Quiz Service — Quiz & Question CRUD.

Class-based service pattern:
- Takes AsyncSession via constructor
- All DB queries are owned by this service
- Raises domain exceptions — never HTTPException
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.quizzes.exceptions import QuestionNotFound, QuizAlreadyExists, QuizNotFound
from src.quizzes.models import Question, Quiz
from src.quizzes.schemas import (
    QuestionCreateRequest,
    QuestionUpdateRequest,
    QuizCreateRequest,
    QuizUpdateRequest,
)


class QuizService:
    """Handles quiz and question CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Quiz CRUD ───────────────────────────────────────────────

    async def create_quiz(self, lesson_id: UUID, data: QuizCreateRequest) -> Quiz:
        """Create a quiz for a lesson. Raises QuizAlreadyExists if one exists."""
        result = await self._db.execute(
            select(Quiz).where(Quiz.lesson_id == lesson_id)
        )
        if result.scalar_one_or_none():
            raise QuizAlreadyExists()

        quiz = Quiz(
            lesson_id=lesson_id,
            title=data.title,
            description=data.description,
            time_limit_minutes=data.time_limit_minutes,
        )
        self._db.add(quiz)
        await self._db.flush()
        return quiz

    async def get_quiz_by_lesson(self, lesson_id: UUID) -> Quiz:
        """Get quiz by lesson ID or raise QuizNotFound."""
        result = await self._db.execute(
            select(Quiz).where(Quiz.lesson_id == lesson_id)
        )
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise QuizNotFound(f"lesson_id={lesson_id}")
        return quiz

    async def get_quiz_by_id(self, quiz_id: UUID) -> Quiz:
        """Get quiz by its own ID or raise QuizNotFound."""
        result = await self._db.execute(select(Quiz).where(Quiz.id == quiz_id))
        quiz = result.scalar_one_or_none()
        if not quiz:
            raise QuizNotFound(quiz_id)
        return quiz

    async def get_quiz_with_questions(
        self, quiz_id: UUID
    ) -> tuple[Quiz, list[Question]]:
        """Load quiz + all its questions. Used by submissions service."""
        quiz = await self.get_quiz_by_id(quiz_id)
        result = await self._db.execute(
            select(Question).where(Question.quiz_id == quiz_id)
        )
        questions = list(result.scalars().all())
        return quiz, questions

    async def update_quiz(self, lesson_id: UUID, data: QuizUpdateRequest) -> Quiz:
        """Update a quiz by lesson ID."""
        quiz = await self.get_quiz_by_lesson(lesson_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quiz, field, value)
        await self._db.flush()
        return quiz

    async def delete_quiz(self, lesson_id: UUID) -> None:
        """Delete a quiz by lesson ID."""
        quiz = await self.get_quiz_by_lesson(lesson_id)
        await self._db.delete(quiz)
        await self._db.flush()

    # ── Question CRUD ───────────────────────────────────────────

    async def add_question(
        self, quiz_id: UUID, data: QuestionCreateRequest
    ) -> Question:
        """Add a question to a quiz."""
        await self.get_quiz_by_id(quiz_id)  # Ensure quiz exists
        question = Question(
            quiz_id=quiz_id,
            text=data.text,
            type=data.type,
            options=data.options,
            correct_answer=data.correct_answer,
        )
        self._db.add(question)
        await self._db.flush()
        return question

    async def get_question_by_id(self, question_id: UUID) -> Question:
        """Get question by ID or raise QuestionNotFound."""
        result = await self._db.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            raise QuestionNotFound(question_id)
        return question

    async def update_question(
        self, question_id: UUID, data: QuestionUpdateRequest
    ) -> Question:
        """Update a question."""
        question = await self.get_question_by_id(question_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        await self._db.flush()
        return question

    async def delete_question(self, question_id: UUID) -> None:
        """Delete a question."""
        question = await self.get_question_by_id(question_id)
        await self._db.delete(question)
        await self._db.flush()

    async def count_questions(self, quiz_id: UUID) -> int:
        """Count questions in a quiz."""
        result = await self._db.execute(
            select(func.count()).select_from(Question).where(
                Question.quiz_id == quiz_id
            )
        )
        return result.scalar_one()
