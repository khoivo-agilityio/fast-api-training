"""
User ORM Model.

The User table stores all platform accounts (admin, instructor, student).
Foreign keys from other modules reference this table by string ("users.id")
to avoid circular imports.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import AuditMixin, Base


class UserRole(StrEnum):
    """Platform user roles."""

    ADMIN = "admin"
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class User(AuditMixin, Base):
    """User account — supports admin, instructor, and student roles."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=UserRole.STUDENT.value)
    password: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)

    def __str__(self) -> str:
        return f"{self.display_name} <{self.email}>"

    # Relationships — used by SQLAdmin for FK dropdowns
    courses: Mapped[list["Course"]] = relationship(  # noqa: F821
        "Course", back_populates="instructor", foreign_keys="Course.instructor_id"
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(  # noqa: F821
        "Enrollment", back_populates="user", foreign_keys="Enrollment.user_id"
    )
    submissions: Mapped[list["Submission"]] = relationship(  # noqa: F821
        "Submission", back_populates="user", foreign_keys="Submission.user_id"
    )
    progress_records: Mapped[list["Progress"]] = relationship(  # noqa: F821
        "Progress", back_populates="user", foreign_keys="Progress.user_id"
    )
