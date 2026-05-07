"""Progress module exceptions."""

from src.exceptions import NotFoundError


class ProgressNotFound(NotFoundError):
    def __init__(self):
        super().__init__(
            detail="Progress record not found",
            error_code="PROGRESS_NOT_FOUND",
        )
