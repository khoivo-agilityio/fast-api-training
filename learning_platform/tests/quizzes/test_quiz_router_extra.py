import pytest
from tests.conftest import (
    create_test_course,
    create_test_instructor,
    create_test_lesson,
    create_test_question,
    create_test_quiz,
)

class TestQuizRouterExtra:
    async def test_update_quiz_200(self, client, async_session):
        instructor = await create_test_instructor(async_session, email="qr_upd@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="Upd Course")
        lesson = await create_test_lesson(async_session, course.id, title="Upd Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="Old Title")

        resp = await client.patch(
            f"/api/v1/lessons/{lesson.id}/quiz",
            json={"title": "New Title"},
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    async def test_update_quiz_403(self, client, async_session):
        owner = await create_test_instructor(async_session, email="qr_upd_own@test.com")
        other = await create_test_instructor(async_session, email="qr_upd_oth@test.com")
        course = await create_test_course(async_session, owner["user"].id, title="Upd Own Course")
        lesson = await create_test_lesson(async_session, course.id, title="Upd Own Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="Old Title")

        resp = await client.patch(
            f"/api/v1/lessons/{lesson.id}/quiz",
            json={"title": "New Title"},
            headers=other["auth_header"],
        )

        assert resp.status_code == 403

    async def test_delete_quiz_204(self, client, async_session):
        instructor = await create_test_instructor(async_session, email="qr_delq@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="DelQ Course")
        lesson = await create_test_lesson(async_session, course.id, title="DelQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="To Delete")

        resp = await client.delete(
            f"/api/v1/lessons/{lesson.id}/quiz",
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 204

    async def test_delete_quiz_403(self, client, async_session):
        owner = await create_test_instructor(async_session, email="qr_delq_own@test.com")
        other = await create_test_instructor(async_session, email="qr_delq_oth@test.com")
        course = await create_test_course(async_session, owner["user"].id, title="DelQ Own Course")
        lesson = await create_test_lesson(async_session, course.id, title="DelQ Own Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="Old Title")

        resp = await client.delete(
            f"/api/v1/lessons/{lesson.id}/quiz",
            headers=other["auth_header"],
        )

        assert resp.status_code == 403

    async def test_add_question_403(self, client, async_session):
        owner = await create_test_instructor(async_session, email="qr_add_own@test.com")
        other = await create_test_instructor(async_session, email="qr_add_oth@test.com")
        course = await create_test_course(async_session, owner["user"].id, title="Add Own Course")
        lesson = await create_test_lesson(async_session, course.id, title="Add Own Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="Quiz")

        resp = await client.post(
            f"/api/v1/quizzes/{quiz.id}/questions",
            json={"text": "Hello?", "type": "text", "correct_answer": "Hi"},
            headers=other["auth_header"],
        )

        assert resp.status_code == 403

    async def test_update_question_200(self, client, async_session):
        instructor = await create_test_instructor(async_session, email="qr_updq@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="UpdQ Course")
        lesson = await create_test_lesson(async_session, course.id, title="UpdQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="UpdQ Quiz")
        question = await create_test_question(async_session, quiz.id, text="Old?")

        resp = await client.patch(
            f"/api/v1/questions/{question.id}",
            json={"text": "New?"},
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 200
        assert resp.json()["text"] == "New?"

    async def test_update_question_403(self, client, async_session):
        owner = await create_test_instructor(async_session, email="qr_updq_own@test.com")
        other = await create_test_instructor(async_session, email="qr_updq_oth@test.com")
        course = await create_test_course(async_session, owner["user"].id, title="UpdQ Own Course")
        lesson = await create_test_lesson(async_session, course.id, title="UpdQ Own Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="Quiz")
        question = await create_test_question(async_session, quiz.id, text="Old?")

        resp = await client.patch(
            f"/api/v1/questions/{question.id}",
            json={"text": "New?"},
            headers=other["auth_header"],
        )

        assert resp.status_code == 403

    async def test_delete_question_403(self, client, async_session):
        owner = await create_test_instructor(async_session, email="qr_delquest_own@test.com")
        other = await create_test_instructor(async_session, email="qr_delquest_oth@test.com")
        course = await create_test_course(async_session, owner["user"].id, title="DelQuest Own Course")
        lesson = await create_test_lesson(async_session, course.id, title="DelQuest Own Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="Quiz")
        question = await create_test_question(async_session, quiz.id, text="Old?")

        resp = await client.delete(
            f"/api/v1/questions/{question.id}",
            headers=other["auth_header"],
        )

        assert resp.status_code == 403

