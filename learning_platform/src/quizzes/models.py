"""Quiz & Question ORM Models.

Quiz belongs to a lesson (one-to-one).
Question belongs to a quiz with multiple-choice or text support.
"""

import uuid
from enum import StrEnum

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class QuestionType(StrEnum):
    """Quiz question types."""

    MCQ = "mcq"
    TEXT = "text"


class Quiz(Base):
    """Quiz — belongs to a lesson. One quiz per lesson."""

    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False, unique=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Using Integer minutes instead of Interval — SQLite doesn't support Interval (gotchas #9)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __str__(self) -> str:
        return self.title

    # Relationships — used by SQLAdmin for FK dropdowns
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="quiz", foreign_keys=[lesson_id])
    # cascade delete: removing a Quiz removes its Questions (avoids NOT NULL violation on quiz_id)
    questions: Mapped[list["Question"]] = relationship(
        "Question", back_populates="quiz", foreign_keys="Question.quiz_id",
        cascade="all, delete-orphan",
    )


class Question(Base):
    """Question — belongs to a quiz. Supports MCQ and text types."""

    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quiz_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        String(10), nullable=False, default=QuestionType.MCQ.value
    )
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)

    def __str__(self) -> str:
        return self.text[:60] + ("..." if len(self.text) > 60 else "")

    # Relationships — used by SQLAdmin for FK dropdowns
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions", foreign_keys=[quiz_id])
