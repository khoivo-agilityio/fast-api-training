"""
Quiz Router — /api/v1/lessons/{lesson_id}/quiz + /api/v1/quizzes/{quiz_id}/questions.

Thin router: no try/except, no DB queries, no business logic.
Parse params → call service → return schema.
"""

from uuid import UUID

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user, require_roles
from src.courses.dependencies import get_course_service
from src.courses.exceptions import NotCourseOwner
from src.courses.service import CourseService
from src.lessons.dependencies import get_lesson_service
from src.lessons.service import LessonService
from src.quizzes.dependencies import get_quiz_service
from src.quizzes.schemas import (
    QuestionAdminResponse,
    QuestionCreateRequest,
    QuestionStudentResponse,
    QuestionUpdateRequest,
    QuizCreateRequest,
    QuizResponse,
    QuizUpdateRequest,
)
from src.quizzes.service import QuizService
from src.users.models import User

router = APIRouter(tags=["quizzes"])


# ── Quiz endpoints ──────────────────────────────────────────────


@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResponse, status_code=201)
async def create_quiz(
    lesson_id: UUID,
    data: QuizCreateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    """Create a quiz for a lesson (owner instructor or admin)."""
    lesson = await lesson_service.get_by_id(lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    quiz = await quiz_service.create_quiz(lesson_id, data)
    question_count = await quiz_service.count_questions(quiz.id)
    response = QuizResponse.model_validate(quiz)
    response.question_count = question_count
    return response


@router.get("/lessons/{lesson_id}/quiz")
async def get_quiz(
    lesson_id: UUID,
    current_user: User = Depends(get_current_user),
    lesson_service: LessonService = Depends(get_lesson_service),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> dict:
    """Get quiz with questions for a lesson. Students see questions without answers."""
    await lesson_service.get_by_id(lesson_id)  # 404 if lesson not found
    quiz = await quiz_service.get_quiz_by_lesson(lesson_id)
    _, questions = await quiz_service.get_quiz_with_questions(quiz.id)

    # Build response — students don't see correct_answer
    if current_user.role == "student":
        question_responses = [
            QuestionStudentResponse.model_validate(q).model_dump() for q in questions
        ]
    else:
        question_responses = [
            QuestionAdminResponse.model_validate(q).model_dump() for q in questions
        ]

    return {
        "id": str(quiz.id),
        "lesson_id": str(quiz.lesson_id),
        "title": quiz.title,
        "description": quiz.description,
        "time_limit_minutes": quiz.time_limit_minutes,
        "questions": question_responses,
    }


@router.patch("/lessons/{lesson_id}/quiz", response_model=QuizResponse)
async def update_quiz(
    lesson_id: UUID,
    data: QuizUpdateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    """Update a quiz (owner instructor or admin)."""
    lesson = await lesson_service.get_by_id(lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    quiz = await quiz_service.update_quiz(lesson_id, data)
    question_count = await quiz_service.count_questions(quiz.id)
    response = QuizResponse.model_validate(quiz)
    response.question_count = question_count
    return response


@router.delete("/lessons/{lesson_id}/quiz", status_code=204)
async def delete_quiz(
    lesson_id: UUID,
    current_user: User = Depends(require_roles("instructor", "admin")),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> None:
    """Delete a quiz (owner instructor or admin)."""
    lesson = await lesson_service.get_by_id(lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    await quiz_service.delete_quiz(lesson_id)


# ── Question endpoints ──────────────────────────────────────────


@router.post(
    "/quizzes/{quiz_id}/questions",
    response_model=QuestionAdminResponse,
    status_code=201,
)
async def add_question(
    quiz_id: UUID,
    data: QuestionCreateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    quiz_service: QuizService = Depends(get_quiz_service),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service),
) -> QuestionAdminResponse:
    """Add a question to a quiz (owner instructor or admin)."""
    quiz = await quiz_service.get_quiz_by_id(quiz_id)
    lesson = await lesson_service.get_by_id(quiz.lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    question = await quiz_service.add_question(quiz_id, data)
    return QuestionAdminResponse.model_validate(question)


@router.patch("/questions/{question_id}", response_model=QuestionAdminResponse)
async def update_question(
    question_id: UUID,
    data: QuestionUpdateRequest,
    current_user: User = Depends(require_roles("instructor", "admin")),
    quiz_service: QuizService = Depends(get_quiz_service),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service),
) -> QuestionAdminResponse:
    """Update a question (owner instructor or admin)."""
    question = await quiz_service.get_question_by_id(question_id)
    quiz = await quiz_service.get_quiz_by_id(question.quiz_id)
    lesson = await lesson_service.get_by_id(quiz.lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    updated = await quiz_service.update_question(question_id, data)
    return QuestionAdminResponse.model_validate(updated)


@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(
    question_id: UUID,
    current_user: User = Depends(require_roles("instructor", "admin")),
    quiz_service: QuizService = Depends(get_quiz_service),
    lesson_service: LessonService = Depends(get_lesson_service),
    course_service: CourseService = Depends(get_course_service),
) -> None:
    """Delete a question (owner instructor or admin)."""
    question = await quiz_service.get_question_by_id(question_id)
    quiz = await quiz_service.get_quiz_by_id(question.quiz_id)
    lesson = await lesson_service.get_by_id(quiz.lesson_id)
    course = await course_service.get_by_id(lesson.course_id)
    if current_user.role != "admin" and course.instructor_id != current_user.id:
        raise NotCourseOwner()
    await quiz_service.delete_question(question_id)
