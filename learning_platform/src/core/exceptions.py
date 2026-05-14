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


# ---------------------------------------------------------------------------
# Storage exceptions
# ---------------------------------------------------------------------------


class UnsupportedFileType(ValidationError):
    """Raised when uploaded file bytes don't match any allowed image format."""

    def __init__(self) -> None:
        super().__init__(
            detail=("Unsupported file type. Allowed formats: JPEG, PNG, GIF, WebP."),
            error_code="UNSUPPORTED_FILE_TYPE",
        )


class FileTooLarge(ValidationError):
    """Raised when the uploaded file exceeds the maximum allowed size."""

    def __init__(self, max_bytes: int) -> None:
        max_mb = max_bytes / (1024 * 1024)
        super().__init__(
            detail=f"File exceeds maximum allowed size of {max_mb:.0f} MB.",
            error_code="FILE_TOO_LARGE",
        )


class StorageObjectNotFound(NotFoundError):
    """Raised when an expected S3 object does not exist."""

    def __init__(self, object_key: str) -> None:
        super().__init__(
            detail=f"Storage object not found: {object_key}",
            error_code="STORAGE_OBJECT_NOT_FOUND",
        )
