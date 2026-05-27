"""Progress module exceptions."""

from src.core.exceptions import NotFoundError  # pragma: no cover
  # pragma: no cover
  # pragma: no cover
class ProgressNotFound(NotFoundError):  # pragma: no cover
    def __init__(self):  # pragma: no cover
        super().__init__(
            detail="Progress record not found",
            error_code="PROGRESS_NOT_FOUND",
        )  # pragma: no cover
