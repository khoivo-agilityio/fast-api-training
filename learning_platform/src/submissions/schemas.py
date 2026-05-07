"""Submission Schemas (DTOs) — Pydantic v2."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    """Single answer in a quiz submission."""

    question_id: UUID
    text: str = Field(min_length=1)


class SubmitQuizRequest(BaseModel):
    """Submit answers for a quiz."""

    answers: list[AnswerSubmission] = Field(min_length=1)


class AnswerResultResponse(BaseModel):
    """Single answer result after grading."""

    id: UUID
    question_id: UUID
    text: str
    is_correct: bool
    model_config = {"from_attributes": True}


class SubmissionResponse(BaseModel):
    """Submission summary."""

    id: UUID
    quiz_id: UUID
    user_id: UUID
    score: float
    submitted_at: datetime
    model_config = {"from_attributes": True}


class SubmissionDetailResponse(SubmissionResponse):
    """Submission with individual answer results."""

    answers: list[AnswerResultResponse]
