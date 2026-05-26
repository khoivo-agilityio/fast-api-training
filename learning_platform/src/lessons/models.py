"""
Lesson ORM Model.

Lessons belong to a course. Each lesson has text content and an ordering
field for display within the course. Foreign keys reference other modules'
tables by string to avoid circular imports.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import AuditMixin, Base


class Lesson(AuditMixin, Base):
    """Lesson — text content belonging to a course."""

    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    timeline: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __str__(self) -> str:
        return self.title

    # Relationships — used by SQLAdmin for FK dropdowns
    course: Mapped["Course"] = relationship(  # noqa: F821
        "Course", back_populates="lessons", foreign_keys=[course_id]
    )
    # cascade delete: removing a Lesson removes its Quiz and Progress records
    quiz: Mapped["Quiz"] = relationship(  # noqa: F821
        "Quiz",
        back_populates="lesson",
        foreign_keys="Quiz.lesson_id",
        uselist=False,
        cascade="all, delete-orphan",
    )
    progress_records: Mapped[list["Progress"]] = relationship(  # noqa: F821
        "Progress",
        back_populates="lesson",
        foreign_keys="Progress.lesson_id",
        cascade="all, delete-orphan",
    )
