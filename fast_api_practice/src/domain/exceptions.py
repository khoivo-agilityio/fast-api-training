# filepath: fast_api_practice/src/domain/exceptions.py
"""
Custom domain exceptions.

These are raised by services and automatically converted to HTTP responses
by the exception handlers registered in ``main.py``.  Routes no longer need
repetitive try/except blocks.
"""


class DomainError(Exception):
    """Base class for all domain-layer exceptions."""


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""


class AuthorizationError(DomainError):
    """Raised when the caller lacks permission for the operation."""


class ConflictError(DomainError):
    """Raised when the operation conflicts with existing state (e.g. duplicate)."""


class DomainValidationError(DomainError):
    """Raised when a business-rule validation fails (bad input, etc.)."""


class AuthenticationError(DomainError):
    """Raised when authentication fails (bad credentials, expired token, etc.)."""
