"""
Submission & Answer ORM Models.

Submission — a student's attempt at a quiz.
Answer     — one question's answer within a submission.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Submission(Base):
    """Student's quiz submission with auto-graded score."""

    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __str__(self) -> str:
        return f"Submission(quiz={self.quiz_id}, score={self.score})"

    # Relationships — used by SQLAdmin for FK dropdowns
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="submissions", foreign_keys=[user_id]
    )
    quiz: Mapped["Quiz"] = relationship("Quiz", foreign_keys=[quiz_id])  # noqa: F821
    # cascade delete: removing a Submission removes its Answers
    # (avoids NOT NULL violation on submission_id)
    answers: Mapped[list["Answer"]] = relationship(
        "Answer",
        back_populates="submission",
        foreign_keys="Answer.submission_id",
        cascade="all, delete-orphan",
    )


class Answer(Base):
    """Individual answer within a submission."""

    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)

    def __str__(self) -> str:
        return self.text[:60] + ("..." if len(self.text) > 60 else "")

    # Relationships — used by SQLAdmin for FK dropdowns
    submission: Mapped["Submission"] = relationship(  # noqa: F821
        "Submission", back_populates="answers", foreign_keys=[submission_id]
    )
    question: Mapped["Question"] = relationship(  # noqa: F821
        "Question", foreign_keys=[question_id]
    )
