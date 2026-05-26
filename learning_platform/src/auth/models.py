"""
Auth ORM Models — Token blacklist.

Stores revoked JWT token IDs (jti) to implement server-side logout
and refresh token rotation. Expired entries can be cleaned up periodically.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import AuditMixin, Base


class BlacklistedToken(AuditMixin, Base):
    """Blacklisted JWT — prevents reuse of revoked access and refresh tokens."""

    __tablename__ = "blacklisted_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __str__(self) -> str:
        return f"BlacklistedToken(jti={self.jti})"
