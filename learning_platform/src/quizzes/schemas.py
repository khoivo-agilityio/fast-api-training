"""Quiz & Question Schemas (DTOs) — Pydantic v2."""

from uuid import UUID

from pydantic import BaseModel, Field


class QuizCreateRequest(BaseModel):
    """Create quiz for a lesson."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    time_limit_minutes: int | None = Field(None, gt=0)


class QuizUpdateRequest(BaseModel):
    """Partial update quiz."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    time_limit_minutes: int | None = None


class QuestionCreateRequest(BaseModel):
    """Add a question to a quiz."""

    text: str = Field(min_length=1)
    type: str = Field(pattern="^(mcq|text)$")
    options: list[str] | None = None
    correct_answer: str = Field(min_length=1)


class QuestionUpdateRequest(BaseModel):
    """Partial update question."""

    text: str | None = None
    type: str | None = Field(None, pattern="^(mcq|text)$")
    options: list[str] | None = None
    correct_answer: str | None = None


class QuestionStudentResponse(BaseModel):
    """Question as seen by students — correct_answer hidden."""

    id: UUID
    quiz_id: UUID
    text: str
    type: str
    options: list[str] | None
    model_config = {"from_attributes": True}


class QuestionAdminResponse(QuestionStudentResponse):
    """Question as seen by instructors/admins — includes correct_answer."""

    correct_answer: str


class QuizResponse(BaseModel):
    """Quiz response without questions list."""

    id: UUID
    lesson_id: UUID
    title: str
    description: str | None
    time_limit_minutes: int | None
    question_count: int = 0
    model_config = {"from_attributes": True}


class QuizDetailResponse(BaseModel):
    """Quiz with questions list (student view)."""

    id: UUID
    lesson_id: UUID
    title: str
    description: str | None
    time_limit_minutes: int | None
    questions: list[QuestionStudentResponse]
    model_config = {"from_attributes": True}
