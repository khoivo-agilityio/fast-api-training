"""
Admin View — SQLAdmin ModelView configurations + AuthenticationBackend.

Merged from:
  - src/admin/views.py   (ModelView classes)
  - src/admin/auth.py    (AdminAuthBackend)

form_columns must reference relationship attributes (not raw FK UUID columns)
so SQLAdmin renders proper dropdown pickers instead of blank text inputs.
"""

from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.auth.jwt import decode_token
from src.auth.security import hash_password
from src.auth.service import AuthService
from src.core.database import async_session_factory
from src.courses.models import Course, Enrollment
from src.lessons.models import Lesson
from src.progress.models import Progress
from src.quizzes.models import Question, Quiz
from src.submissions.models import Answer, Submission
from src.users.models import User

# ---------------------------------------------------------------------------
# Authentication Backend
# ---------------------------------------------------------------------------


class AdminAuthBackend(AuthenticationBackend):
    """Session-based auth for SQLAdmin UI. Only admin users can access."""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username", "")
        password = form.get("password", "")

        async with async_session_factory() as session:
            service = AuthService(session)
            try:
                tokens = await service.login(str(email), str(password))
                payload = decode_token(tokens.access_token)
                if payload.get("role") != "admin":
                    return False
                request.session.update(
                    {
                        "token": tokens.access_token,
                        "user_id": payload["sub"],
                    }
                )
                await session.commit()
                return True
            except Exception:
                return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        try:
            payload = decode_token(token)
            return payload.get("role") == "admin"
        except Exception:
            return False


# ---------------------------------------------------------------------------
# ModelViews
# ---------------------------------------------------------------------------


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.role, User.display_name, User.created_at]
    column_searchable_list = [User.email, User.display_name]
    form_columns = [User.email, User.role, User.display_name, User.password, User.avatar]
    can_create = True
    can_edit = True
    can_delete = True
    name = "User"
    name_plural = "Users"

    async def on_model_change(self, data: dict, model: User, is_created: bool, request: Request) -> None:
        """Hash the password before saving to the database."""
        if "password" in data and data["password"]:
            data["password"] = await hash_password(data["password"])


class CourseAdmin(ModelView, model=Course):
    column_list = [Course.id, Course.title, Course.instructor_id, Course.created_at]
    column_searchable_list = [Course.title]
    # Use relationship 'instructor' so SQLAdmin renders a User dropdown
    form_columns = [Course.instructor, Course.title, Course.description]
    name = "Course"
    name_plural = "Courses"


class EnrollmentAdmin(ModelView, model=Enrollment):
    column_list = [Enrollment.id, Enrollment.user_id, Enrollment.course_id, Enrollment.created_at]
    # Use relationships 'user' and 'course' for dropdowns
    form_columns = [Enrollment.user, Enrollment.course]
    name = "Enrollment"
    name_plural = "Enrollments"


class LessonAdmin(ModelView, model=Lesson):
    column_list = [Lesson.id, Lesson.course_id, Lesson.title, Lesson.order]
    column_searchable_list = [Lesson.title]
    # Use relationship 'course' for Course dropdown
    form_columns = [Lesson.course, Lesson.title, Lesson.content, Lesson.order, Lesson.timeline]
    name = "Lesson"
    name_plural = "Lessons"


class QuizAdmin(ModelView, model=Quiz):
    column_list = [Quiz.id, Quiz.lesson_id, Quiz.title]
    # Use relationship 'lesson' so SQLAdmin renders a Lesson dropdown
    form_columns = [Quiz.lesson, Quiz.title, Quiz.description, Quiz.time_limit_minutes]
    # Custom template adds a cascading Course → Lesson dropdown via JS
    create_template = "sqladmin/quiz_create.html"
    name = "Quiz"
    name_plural = "Quizzes"


class QuestionAdmin(ModelView, model=Question):
    column_list = [Question.id, Question.quiz_id, Question.text, Question.type]
    # Use relationship 'quiz' for Quiz dropdown
    form_columns = [
        Question.quiz,
        Question.text,
        Question.type,
        Question.options,
        Question.correct_answer,
    ]

    # Placeholders shown inside each input
    form_widget_args = {
        "text": {
            "placeholder": "e.g. What is the output of print(type([]))?",
            "rows": 3,
        },
        "type": {
            "placeholder": "mcq  or  text",
        },
        "options": {
            "placeholder": (
                "[\"<class 'list'>\", \"<class 'tuple'>\","
                " \"<class 'dict'>\", \"<class 'set'>\"]);"
            ),
            "rows": 4,
        },
        "correct_answer": {
            "placeholder": "e.g. <class 'list'>   ← must exactly match one entry in options",
        },
    }

    # Helper text rendered below each field label
    column_descriptions = {
        "type": (
            '"mcq" — multiple choice (requires options + correct_answer).  '
            '"text" — free-text answer (options can be left empty).'
        ),
        "options": (
            "JSON array of answer strings. Example: "
            "[\"<class 'list'>\", \"<class 'tuple'>\", \"<class 'dict'>\", \"<class 'set'>\"]  "
            "— leave empty for text-type questions."
        ),
        "correct_answer": (
            "For MCQ: the exact string from options that is correct. "
            "For text: the expected answer string used for grading."
        ),
    }

    name = "Question"
    name_plural = "Questions"


class SubmissionAdmin(ModelView, model=Submission):
    column_list = [Submission.id, Submission.user_id, Submission.quiz_id, Submission.score]
    form_columns = [Submission.user, Submission.quiz, Submission.score]
    name = "Submission"
    name_plural = "Submissions"


class AnswerAdmin(ModelView, model=Answer):
    column_list = [Answer.id, Answer.submission_id, Answer.question_id, Answer.is_correct]
    form_columns = [Answer.submission, Answer.question, Answer.text, Answer.is_correct]
    name = "Answer"
    name_plural = "Answers"


class ProgressAdmin(ModelView, model=Progress):
    column_list = [Progress.id, Progress.user_id, Progress.lesson_id, Progress.status]
    form_columns = [Progress.user, Progress.lesson, Progress.status]
    name = "Progress"
    name_plural = "Progress Records"
