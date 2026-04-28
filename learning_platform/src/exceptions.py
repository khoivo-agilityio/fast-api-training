"""Shared domain exception hierarchy.

All module-specific exceptions should subclass one of these base classes.
Global exception handlers in main.py map them to JSON responses.
"""


class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__.upper()


class NotFoundError(DomainError):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, "NOT_FOUND")


class AuthorizationError(DomainError):
    """Forbidden action."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class AuthenticationError(DomainError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class ConflictError(DomainError):
    """Resource already exists or state conflict."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message, "CONFLICT")


class ValidationError(DomainError):
    """Business rule validation failed."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, "VALIDATION_ERROR")
