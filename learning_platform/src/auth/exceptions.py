"""Auth-specific domain exceptions."""

from src.exceptions import AuthenticationError


class InvalidCredentials(AuthenticationError):
    """Invalid email or password."""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message)
        self.error_code = "INVALID_CREDENTIALS"


class TokenRevoked(AuthenticationError):
    """Token has been revoked/blacklisted."""

    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message)
        self.error_code = "TOKEN_REVOKED"


class TokenExpired(AuthenticationError):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)
        self.error_code = "TOKEN_EXPIRED"


class InvalidToken(AuthenticationError):
    """Token is malformed or invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)
        self.error_code = "INVALID_TOKEN"
