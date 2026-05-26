"""Progress ORM Model — tracks lesson-level completion per user."""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import AuditMixin, Base


class ProgressStatus(StrEnum):
    """Lesson progress states."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Progress(AuditMixin, Base):
    """Progress — tracks one user's progress on one lesson."""

    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        SAEnum(ProgressStatus, name="progressstatus", native_enum=True, create_constraint=True),
        nullable=False,
        default=ProgressStatus.NOT_STARTED,
    )
    accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __str__(self) -> str:
        return f"Progress(user={self.user_id}, lesson={self.lesson_id}, status={self.status})"

    # Relationships — used by SQLAdmin for FK dropdowns
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="progress_records", foreign_keys=[user_id]
    )
    lesson: Mapped["Lesson"] = relationship(  # noqa: F821
        "Lesson", back_populates="progress_records", foreign_keys=[lesson_id]
    )
