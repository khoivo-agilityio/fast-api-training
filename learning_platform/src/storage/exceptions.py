"""Storage module exceptions."""

from src.exceptions import NotFoundError, ValidationError


class UnsupportedFileType(ValidationError):
    """Raised when uploaded file bytes don't match any allowed image format."""

    def __init__(self) -> None:
        super().__init__(
            detail=(
                "Unsupported file type. "
                "Allowed formats: JPEG, PNG, GIF, WebP."
            ),
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
