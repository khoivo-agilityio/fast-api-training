"""
Tests for Quiz Router — HTTP endpoint tests for quiz & question CRUD.
"""

from tests.conftest import (
    create_test_course,
    create_test_enrollment,
    create_test_instructor,
    create_test_lesson,
    create_test_question,
    create_test_quiz,
    create_test_user,
)


class TestQuizRouter:
    """Quiz endpoint tests."""

    async def test_create_quiz_201_instructor(self, client, async_session):
        """Instructor creates quiz for own lesson → 201."""
        instructor = await create_test_instructor(async_session, email="qr_ci@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QR CI Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QR CI Lesson")

        resp = await client.post(
            f"/api/v1/lessons/{lesson.id}/quiz",
            json={"title": "Router Quiz", "description": "Test desc"},
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Router Quiz"
        assert data["lesson_id"] == str(lesson.id)

    async def test_create_quiz_409_duplicate(self, client, async_session):
        """Creating a second quiz for the same lesson → 409."""
        instructor = await create_test_instructor(async_session, email="qr_dup@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QR Dup Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QR Dup Lesson")
        await create_test_quiz(async_session, lesson.id, title="Existing Quiz")

        resp = await client.post(
            f"/api/v1/lessons/{lesson.id}/quiz",
            json={"title": "Another Quiz"},
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 409

    async def test_get_quiz_200(self, client, async_session):
        """Get quiz with questions → 200."""
        instructor = await create_test_instructor(async_session, email="qr_gq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QR GQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QR GQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="GQ Quiz")
        await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A1")

        resp = await client.get(
            f"/api/v1/lessons/{lesson.id}/quiz",
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "GQ Quiz"
        assert len(data["questions"]) == 1
        # Instructor sees correct_answer
        assert "correct_answer" in data["questions"][0]

    async def test_get_quiz_200_student_hides_answers(self, client, async_session):
        """Student gets quiz → questions don't include correct_answer."""
        instructor = await create_test_instructor(async_session, email="qr_sh@test.com")
        student = await create_test_user(async_session, email="qr_sh_s@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QR SH Course"
        )
        await create_test_enrollment(async_session, student["user"].id, course.id)
        lesson = await create_test_lesson(async_session, course.id, title="QR SH Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="SH Quiz")
        await create_test_question(async_session, quiz.id, text="Q1?", correct_answer="A1")

        resp = await client.get(
            f"/api/v1/lessons/{lesson.id}/quiz",
            headers=student["auth_header"],
        )

        assert resp.status_code == 200
        data = resp.json()
        # Student should NOT see correct_answer
        assert "correct_answer" not in data["questions"][0]

    async def test_get_quiz_404(self, client, async_session):
        """Get quiz for lesson without quiz → 404."""
        instructor = await create_test_instructor(async_session, email="qr_404@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QR 404 Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QR 404 Lesson")

        resp = await client.get(
            f"/api/v1/lessons/{lesson.id}/quiz",
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 404

    async def test_create_quiz_403_wrong_instructor(self, client, async_session):
        """Instructor creating quiz for another instructor's lesson → 403."""
        owner = await create_test_instructor(async_session, email="qr_own@test.com")
        other = await create_test_instructor(async_session, email="qr_other@test.com")
        course = await create_test_course(
            async_session, owner["user"].id, title="QR Own Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QR Own Lesson")

        resp = await client.post(
            f"/api/v1/lessons/{lesson.id}/quiz",
            json={"title": "Stolen Quiz"},
            headers=other["auth_header"],
        )

        assert resp.status_code == 403

    async def test_add_question_201(self, client, async_session):
        """Add question to quiz → 201."""
        instructor = await create_test_instructor(async_session, email="qr_addq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QR AddQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QR AddQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="AddQ Quiz")

        resp = await client.post(
            f"/api/v1/quizzes/{quiz.id}/questions",
            json={
                "text": "What is 3+3?",
                "type": "mcq",
                "options": ["5", "6", "7"],
                "correct_answer": "6",
            },
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["text"] == "What is 3+3?"
        assert data["correct_answer"] == "6"

    async def test_delete_question_204(self, client, async_session):
        """Delete a question → 204."""
        instructor = await create_test_instructor(async_session, email="qr_delq@test.com")
        course = await create_test_course(
            async_session, instructor["user"].id, title="QR DelQ Course"
        )
        lesson = await create_test_lesson(async_session, course.id, title="QR DelQ Lesson")
        quiz = await create_test_quiz(async_session, lesson.id, title="DelQ Quiz")
        question = await create_test_question(async_session, quiz.id)

        resp = await client.delete(
            f"/api/v1/questions/{question.id}",
            headers=instructor["auth_header"],
        )

        assert resp.status_code == 204
