import pytest
from uuid import uuid4
from src.submissions.service import SubmissionService
from src.submissions.exceptions import SubmissionNotFound
from src.core.exceptions import ValidationError
from src.submissions.schemas import SubmitQuizRequest, AnswerSubmission
from src.quizzes.service import QuizService
from src.lessons.service import LessonService
from src.courses.service import CourseService
from src.progress.service import ProgressService
from tests.conftest import (
    create_test_course,
    create_test_enrollment,
    create_test_instructor,
    create_test_lesson,
    create_test_question,
    create_test_quiz,
    create_test_user,
    create_test_admin,
)

class TestSubmissionServiceExtra:
    async def test_list_all(self, async_session):
        service = SubmissionService(async_session)
        items = await service.list_all()
        assert isinstance(items, list)

    async def test_get_user_submission_not_found(self, async_session):
        service = SubmissionService(async_session)
        with pytest.raises(SubmissionNotFound):
            await service.get_user_submission(uuid4(), uuid4())

    async def test_get_submission_with_answers_not_found(self, async_session):
        service = SubmissionService(async_session)
        with pytest.raises(SubmissionNotFound):
            await service.get_submission_with_answers(uuid4(), uuid4())

    async def test_delete_submission(self, client, async_session):
        quiz_svc = QuizService(async_session)
        lesson_svc = LessonService(async_session)
        course_svc = CourseService(async_session)
        progress_svc = ProgressService(async_session)

        student = await create_test_user(async_session, email="sub_del@test.com")
        instructor = await create_test_instructor(async_session, email="sub_del_i@test.com")
        course = await create_test_course(async_session, instructor["user"].id)
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        service = SubmissionService(async_session)
        req = SubmitQuizRequest(answers=[AnswerSubmission(question_id=q1.id, text="A")])
        submission = await service.submit(
            quiz.id, student["user"].id, req,
            quiz_service=quiz_svc, lesson_service=lesson_svc,
            course_service=course_svc, progress_service=progress_svc
        )

        admin = await create_test_admin(async_session, email="adm_del_sub@admintest.com")
        # delete via router
        resp = await client.delete(
            f"/api/v1/admin/submissions/{submission.id}",
            headers=admin["auth_header"],
        )
        assert resp.status_code == 204

    async def test_duplicate_answers(self, async_session):
        quiz_svc = QuizService(async_session)
        lesson_svc = LessonService(async_session)
        course_svc = CourseService(async_session)
        progress_svc = ProgressService(async_session)

        student = await create_test_user(async_session, email="sub_dup@test.com")
        instructor = await create_test_instructor(async_session, email="sub_dup_i@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SubDup Course")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id, title="SubDup Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="SubDup Quiz")
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        service = SubmissionService(async_session)
        req = SubmitQuizRequest(answers=[
            AnswerSubmission(question_id=q1.id, text="A"),
            AnswerSubmission(question_id=q1.id, text="A"),
        ])
        with pytest.raises(ValidationError) as exc_info:
            await service.submit(
                quiz.id, student["user"].id, req,
                quiz_service=quiz_svc,
                lesson_service=lesson_svc,
                course_service=course_svc,
                progress_service=progress_svc
            )
        assert exc_info.value.error_code == "DUPLICATE_ANSWERS"

    async def test_unknown_questions(self, async_session):
        quiz_svc = QuizService(async_session)
        lesson_svc = LessonService(async_session)
        course_svc = CourseService(async_session)
        progress_svc = ProgressService(async_session)

        student = await create_test_user(async_session, email="sub_unk@test.com")
        instructor = await create_test_instructor(async_session, email="sub_unk_i@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SubUnk Course")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id, title="SubUnk Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="SubUnk Quiz")
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        service = SubmissionService(async_session)
        req = SubmitQuizRequest(answers=[
            AnswerSubmission(question_id=q1.id, text="A"),
            AnswerSubmission(question_id=uuid4(), text="B"),
        ])
        with pytest.raises(ValidationError) as exc_info:
            await service.submit(
                quiz.id, student["user"].id, req,
                quiz_service=quiz_svc,
                lesson_service=lesson_svc,
                course_service=course_svc,
                progress_service=progress_svc
            )
        assert exc_info.value.error_code == "UNKNOWN_QUESTIONS"

    async def test_missing_answers(self, async_session):
        quiz_svc = QuizService(async_session)
        lesson_svc = LessonService(async_session)
        course_svc = CourseService(async_session)
        progress_svc = ProgressService(async_session)

        student = await create_test_user(async_session, email="sub_mis@test.com")
        instructor = await create_test_instructor(async_session, email="sub_mis_i@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SubMis Course")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id, title="SubMis Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="SubMis Quiz")
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")
        q2 = await create_test_question(async_session, quiz.id, text="Q2?", correct_answer="B")

        service = SubmissionService(async_session)
        req = SubmitQuizRequest(answers=[
            AnswerSubmission(question_id=q1.id, text="A"),
        ])
        with pytest.raises(ValidationError) as exc_info:
            await service.submit(
                quiz.id, student["user"].id, req,
                quiz_service=quiz_svc,
                lesson_service=lesson_svc,
                course_service=course_svc,
                progress_service=progress_svc
            )
        assert exc_info.value.error_code == "MISSING_ANSWERS"

