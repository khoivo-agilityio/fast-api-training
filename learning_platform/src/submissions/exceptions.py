"""Submission module exceptions."""

from src.exceptions import ConflictError, NotFoundError


class AlreadySubmitted(ConflictError):
    def __init__(self):
        super().__init__(
            detail="You have already submitted this quiz",
            error_code="ALREADY_SUBMITTED",
        )


class SubmissionNotFound(NotFoundError):
    def __init__(self, identifier: object = None):
        detail = (
            f"Submission not found: {identifier}"
            if identifier
            else "Submission not found"
        )
        super().__init__(detail=detail, error_code="SUBMISSION_NOT_FOUND")
