"""
Tests for Quiz Service — CRUD operations for quizzes and questions.
"""

import pytest

from src.quizzes.exceptions import QuestionNotFound, QuizAlreadyExists, QuizNotFound
from src.quizzes.schemas import QuestionCreateRequest, QuizCreateRequest
from src.quizzes.service import QuizService
from tests.conftest import (
    create_test_course,
    create_test_instructor,
    create_test_lesson,
    create_test_question,
    create_test_quiz,
)


class TestQuizService:
    """Quiz CRUD tests."""

    async def test_create_quiz(self, async_session):
        """Instructor creates quiz for a lesson."""
        instructor = await create_test_instructor(async_session, email="qs_i@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS Lesson")

        service = QuizService(async_session)
        data = QuizCreateRequest(title="My Quiz", description="A quiz", time_limit_minutes=30)
        quiz = await service.create_quiz(lesson.id, data)

        assert quiz.title == "My Quiz"
        assert quiz.description == "A quiz"
        assert quiz.time_limit_minutes == 30
        assert quiz.lesson_id == lesson.id

    async def test_create_quiz_duplicate(self, async_session):
        """Creating a second quiz for the same lesson raises QuizAlreadyExists."""
        instructor = await create_test_instructor(async_session, email="qs_dup@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS Dup Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS Dup Lesson")
        await create_test_quiz(async_session, lesson.id, title="First Quiz")

        service = QuizService(async_session)
        data = QuizCreateRequest(title="Second Quiz")
        with pytest.raises(QuizAlreadyExists):
            await service.create_quiz(lesson.id, data)

    async def test_get_quiz_by_lesson_found(self, async_session):
        """Get quiz by lesson ID when it exists."""
        instructor = await create_test_instructor(async_session, email="qs_gl@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS GL Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS GL Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="Found Quiz")

        service = QuizService(async_session)
        found = await service.get_quiz_by_lesson(lesson.id)

        assert found.id == quiz.id
        assert found.title == "Found Quiz"

    async def test_get_quiz_by_lesson_not_found(self, async_session):
        """Get quiz by lesson ID raises QuizNotFound when no quiz exists."""
        import uuid

        service = QuizService(async_session)
        with pytest.raises(QuizNotFound):
            await service.get_quiz_by_lesson(uuid.uuid4())

    async def test_get_quiz_with_questions(self, async_session):
        """Get quiz with all its questions."""
        instructor = await create_test_instructor(async_session, email="qs_wq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS WQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS WQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="WQ Quiz")
        await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A1")
        await create_test_question(async_session, quiz.id, text="Q2?", correct_answer="A2")

        service = QuizService(async_session)
        found_quiz, questions = await service.get_quiz_with_questions(quiz.id)

        assert found_quiz.id == quiz.id
        assert len(questions) == 2

    async def test_add_question(self, async_session):
        """Add a question to a quiz."""
        instructor = await create_test_instructor(async_session, email="qs_aq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS AQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS AQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="AQ Quiz")

        service = QuizService(async_session)
        data = QuestionCreateRequest(
            text="What is 1+1?", type="mcq", options=["1", "2", "3"], correct_answer="2"
        )
        question = await service.add_question(quiz.id, data)

        assert question.text == "What is 1+1?"
        assert question.correct_answer == "2"
        assert question.quiz_id == quiz.id

    async def test_update_question(self, async_session):
        """Update a question's text."""
        instructor = await create_test_instructor(async_session, email="qs_uq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS UQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS UQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="UQ Quiz")
        question = await create_test_question(
            async_session, quiz.id, text="Old Q?", correct_answer="Old A"
        )

        from src.quizzes.schemas import QuestionUpdateRequest

        service = QuizService(async_session)
        updated = await service.update_question(
            question.id, QuestionUpdateRequest(text="New Q?", correct_answer="New A")
        )

        assert updated.text == "New Q?"
        assert updated.correct_answer == "New A"

    async def test_delete_question(self, async_session):
        """Delete a question."""
        instructor = await create_test_instructor(async_session, email="qs_dq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS DQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS DQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="DQ Quiz")
        question = await create_test_question(async_session, quiz.id)

        service = QuizService(async_session)
        await service.delete_question(question.id)

        with pytest.raises(QuestionNotFound):
            await service.get_question_by_id(question.id)

    async def test_count_questions(self, async_session):
        """Count questions in a quiz."""
        instructor = await create_test_instructor(async_session, email="qs_cq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QS CQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QS CQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="CQ Quiz")
        await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A1")
        await create_test_question(async_session, quiz.id, text="Q2?", correct_answer="A2")
        await create_test_question(async_session, quiz.id, text="Q3?", correct_answer="A3")

        service = QuizService(async_session)
        count = await service.count_questions(quiz.id)

        assert count == 3
