"""User module exceptions."""

from src.exceptions import NotFoundError


class UserNotFound(NotFoundError):
    """Raised when a user is not found by ID or email."""

    def __init__(self, identifier: object = None):
        detail = f"User not found: {identifier}" if identifier else "User not found"
        super().__init__(detail=detail, error_code="USER_NOT_FOUND")
