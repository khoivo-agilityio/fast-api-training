import pytest
from uuid import uuid4
from src.quizzes.service import QuizService
from src.quizzes.exceptions import QuizNotFound
from src.quizzes.schemas import QuizUpdateRequest

class TestQuizServiceExtra:
    async def test_get_quiz_by_id_not_found(self, async_session):
        service = QuizService(async_session)
        with pytest.raises(QuizNotFound):
            await service.get_quiz_by_id(uuid4())

    async def test_has_quiz_for_lesson(self, async_session):
        service = QuizService(async_session)
        assert await service.has_quiz_for_lesson(uuid4()) is False

    async def test_update_quiz_direct(self, async_session):
        from tests.conftest import create_test_course, create_test_lesson, create_test_quiz, create_test_instructor
        quiz_svc = QuizService(async_session)
        instructor = await create_test_instructor(async_session, email="qs_upd_dir@test.com")
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id, title="Old")
        
        updated = await quiz_svc.update_quiz(lesson.id, QuizUpdateRequest(title="New"))
        assert updated.title == "New"

    async def test_delete_quiz_direct(self, async_session):
        from tests.conftest import create_test_course, create_test_lesson, create_test_quiz, create_test_instructor
        quiz_svc = QuizService(async_session)
        instructor = await create_test_instructor(async_session, email="qs_del_dir@test.com")
        course = await create_test_course(async_session, instructor["user"].id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id, title="Old")
        
        await quiz_svc.delete_quiz(lesson.id)
        assert await quiz_svc.has_quiz_for_lesson(lesson.id) is False
