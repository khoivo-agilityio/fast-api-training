"""
Course & Enrollment ORM Models.

The Course table stores platform courses owned by instructors.
The Enrollment table is a many-to-many join between users (students) and courses.
Foreign keys reference other modules' tables by string to avoid circular imports.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Course(Base):
    """Course — created by instructors, enrolled by students."""

    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instructor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __str__(self) -> str:
        return self.title

    # Relationships — used by SQLAdmin for FK dropdowns
    instructor: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="courses", foreign_keys=[instructor_id]
    )
    # cascade delete: removing a Course removes all its Lessons and Enrollments
    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        "Lesson",
        back_populates="course",
        foreign_keys="Lesson.course_id",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # noqa: F821
        "Enrollment",
        back_populates="course",
        foreign_keys="Enrollment.course_id",
        cascade="all, delete-orphan",
    )


class Enrollment(Base):
    """Enrollment — many-to-many join between students and courses."""

    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enrollment_user_course"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __str__(self) -> str:
        return f"Enrollment({self.user_id} → {self.course_id})"

    # Relationships — used by SQLAdmin for FK dropdowns
    user: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="enrollments", foreign_keys=[user_id]
    )
    course: Mapped["Course"] = relationship(  # noqa: F821
        "Course", back_populates="enrollments", foreign_keys=[course_id]
    )
