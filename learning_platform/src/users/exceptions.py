"""User-specific domain exceptions."""

from src.exceptions import NotFoundError


class UserNotFound(NotFoundError):
    """User was not found."""

    def __init__(self, message: str = "User not found"):
        super().__init__(message)
