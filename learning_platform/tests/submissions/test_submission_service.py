"""
Tests for Submission Service — quiz submission and auto-grading.
"""

import pytest

from src.submissions.exceptions import AlreadySubmitted
from src.submissions.schemas import AnswerSubmission, SubmitQuizRequest
from src.submissions.service import SubmissionService
from tests.conftest import (
    create_test_course,
    create_test_enrollment,
    create_test_instructor,
    create_test_lesson,
    create_test_question,
    create_test_quiz,
    create_test_user,
)


class TestSubmissionService:
    async def test_submit_all_correct(self, async_session):
        instructor = await create_test_instructor(async_session, email="ss_ac@test.com")
        student = await create_test_user(async_session, email="ss_acs@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SS AC")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")
        q2 = await create_test_question(async_session, quiz.id, text="Q2?", correct_answer="B")

        service = SubmissionService(async_session)
        data = SubmitQuizRequest(answers=[
            AnswerSubmission(question_id=q1.id, text="A"),
            AnswerSubmission(question_id=q2.id, text="B"),
        ])
        result = await service.submit(quiz.id, student["user"].id, data)
        assert result.score == 100.0
        assert all(a.is_correct for a in result.answers)

    async def test_submit_partial(self, async_session):
        instructor = await create_test_instructor(async_session, email="ss_p@test.com")
        student = await create_test_user(async_session, email="ss_ps@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SS P")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="Right")
        q2 = await create_test_question(
            async_session, quiz.id, text="Q2?", correct_answer="Correct"
        )

        service = SubmissionService(async_session)
        data = SubmitQuizRequest(answers=[
            AnswerSubmission(question_id=q1.id, text="Right"),
            AnswerSubmission(question_id=q2.id, text="Wrong"),
        ])
        result = await service.submit(quiz.id, student["user"].id, data)
        assert result.score == 50.0

    async def test_submit_duplicate(self, async_session):
        instructor = await create_test_instructor(async_session, email="ss_d@test.com")
        student = await create_test_user(async_session, email="ss_ds@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SS D")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        service = SubmissionService(async_session)
        data = SubmitQuizRequest(answers=[AnswerSubmission(question_id=q1.id, text="A")])
        await service.submit(quiz.id, student["user"].id, data)
        with pytest.raises(AlreadySubmitted):
            await service.submit(quiz.id, student["user"].id, data)

    async def test_submit_not_enrolled(self, async_session):
        from src.courses.exceptions import NotEnrolled
        instructor = await create_test_instructor(async_session, email="ss_ne@test.com")
        student = await create_test_user(async_session, email="ss_nes@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SS NE")
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        service = SubmissionService(async_session)
        data = SubmitQuizRequest(answers=[AnswerSubmission(question_id=q1.id, text="A")])
        with pytest.raises(NotEnrolled):
            await service.submit(quiz.id, student["user"].id, data)

    async def test_submit_passing_marks_completed(self, async_session):
        instructor = await create_test_instructor(async_session, email="ss_mc@test.com")
        student = await create_test_user(async_session, email="ss_mcs@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SS MC")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        service = SubmissionService(async_session)
        data = SubmitQuizRequest(answers=[AnswerSubmission(question_id=q1.id, text="A")])
        result = await service.submit(quiz.id, student["user"].id, data)
        assert result.score == 100.0

        from src.progress.models import ProgressStatus
        from src.progress.service import ProgressService
        ps = ProgressService(async_session)
        progress = await ps.get_lesson_progress(student["user"].id, lesson.id)
        assert progress is not None
        assert progress.status == ProgressStatus.COMPLETED
