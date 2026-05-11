"""Tests for Submission Router — HTTP endpoint tests."""

from tests.conftest import (
    create_test_course,
    create_test_enrollment,
    create_test_instructor,
    create_test_lesson,
    create_test_question,
    create_test_quiz,
    create_test_user,
)


class TestSubmissionRouter:
    async def test_submit_201(self, client, async_session):
        instructor = await create_test_instructor(async_session, email="sr_s@test.com")
        student = await create_test_user(async_session, email="sr_ss@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SR S")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        resp = await client.post(
            f"/api/v1/quizzes/{quiz.id}/submit",
            json={"answers": [{"question_id": str(q1.id), "text": "A"}]},
            headers=student["auth_header"],
        )
        assert resp.status_code == 201
        assert resp.json()["score"] == 100.0

    async def test_submit_409_duplicate(self, client, async_session):
        instructor = await create_test_instructor(async_session, email="sr_d@test.com")
        student = await create_test_user(async_session, email="sr_ds@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SR D")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        body = {"answers": [{"question_id": str(q1.id), "text": "A"}]}
        await client.post(
            f"/api/v1/quizzes/{quiz.id}/submit",
            json=body,
            headers=student["auth_header"],
        )
        resp = await client.post(
            f"/api/v1/quizzes/{quiz.id}/submit",
            json=body,
            headers=student["auth_header"],
        )
        assert resp.status_code == 409

    async def test_get_submission_200(self, client, async_session):
        instructor = await create_test_instructor(async_session, email="sr_g@test.com")
        student = await create_test_user(async_session, email="sr_gs@test.com")
        course = await create_test_course(async_session, instructor["user"].id, title="SR G")
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id)
        quiz = await create_test_quiz(async_session, lesson.id)
        q1 = await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A")

        await client.post(
            f"/api/v1/quizzes/{quiz.id}/submit",
            json={"answers": [{"question_id": str(q1.id), "text": "A"}]},
            headers=student["auth_header"],
        )
        resp = await client.get(
            f"/api/v1/quizzes/{quiz.id}/submission",
            headers=student["auth_header"],
        )
        assert resp.status_code == 200
        assert resp.json()["score"] == 100.0
        assert len(resp.json()["answers"]) == 1

    async def test_get_submission_404(self, client, async_session):
        import uuid

        student = await create_test_user(async_session, email="sr_404@test.com")
        fake_id = uuid.uuid4()
        resp = await client.get(
            f"/api/v1/quizzes/{fake_id}/submission",
            headers=student["auth_header"],
        )
        assert resp.status_code == 404
