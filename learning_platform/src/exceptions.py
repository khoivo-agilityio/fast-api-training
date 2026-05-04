"""
Domain Exception Hierarchy.

Services raise these exceptions. Global exception handlers in main.py
convert them to HTTP JSON responses. Route handlers have NO try/except.

MRO-aware status resolution (see gotchas.md #2):
    Use _resolve_status(exc) which walks the class MRO to find the first
    matching parent class in _STATUS_MAP. This avoids the bug where
    subclass exceptions (e.g. InvalidCredentials) miss their parent's
    mapped status code.
"""


class DomainError(Exception):
    """Base class for all domain-specific errors."""

    def __init__(self, detail: str = "An error occurred", error_code: str = "DOMAIN_ERROR"):
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundError(DomainError):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(detail=detail, error_code=error_code)


class AuthenticationError(DomainError):
    """Authentication failed."""

    def __init__(
        self,
        detail: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_ERROR",
    ):
        super().__init__(detail=detail, error_code=error_code)


class AuthorizationError(DomainError):
    """Insufficient permissions."""

    def __init__(
        self,
        detail: str = "Insufficient permissions",
        error_code: str = "AUTHORIZATION_ERROR",
    ):
        super().__init__(detail=detail, error_code=error_code)


class ConflictError(DomainError):
    """Resource conflict (duplicate, already exists)."""

    def __init__(self, detail: str = "Resource conflict", error_code: str = "CONFLICT"):
        super().__init__(detail=detail, error_code=error_code)


class ValidationError(DomainError):
    """Business rule validation failure."""

    def __init__(
        self,
        detail: str = "Validation error",
        error_code: str = "VALIDATION_ERROR",
    ):
        super().__init__(detail=detail, error_code=error_code)
