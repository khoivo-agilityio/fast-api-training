"""Auth module exceptions — specific authentication/authorization errors."""

from src.exceptions import AuthenticationError, ConflictError


class InvalidCredentials(AuthenticationError):
    """Raised when email or password is incorrect."""

    def __init__(self):
        super().__init__(
            detail="Invalid email or password",
            error_code="INVALID_CREDENTIALS",
        )


class EmailAlreadyRegistered(ConflictError):
    """Raised when attempting to register with an already-used email."""

    def __init__(self, email: str = ""):
        detail = f"Email already registered: {email}" if email else "Email already registered"
        super().__init__(detail=detail, error_code="EMAIL_ALREADY_REGISTERED")


class TokenExpired(AuthenticationError):
    """Raised when a JWT token has expired."""

    def __init__(self):
        super().__init__(
            detail="Token has expired",
            error_code="TOKEN_EXPIRED",
        )


class TokenInvalid(AuthenticationError):
    """Raised when a JWT token is malformed or has an invalid signature."""

    def __init__(self):
        super().__init__(
            detail="Invalid token",
            error_code="TOKEN_INVALID",
        )


class TokenRevoked(AuthenticationError):
    """Raised when a JWT token has been blacklisted (logged out)."""

    def __init__(self):
        super().__init__(
            detail="Token has been revoked",
            error_code="TOKEN_REVOKED",
        )


class InsufficientPermissions(AuthenticationError):
    """Raised when the user lacks the required role."""

    def __init__(self, required_roles: list[str] | None = None):
        detail = "Insufficient permissions"
        if required_roles:
            detail = f"Requires one of: {', '.join(required_roles)}"
        super().__init__(
            detail=detail,
            error_code="INSUFFICIENT_PERMISSIONS",
        )
