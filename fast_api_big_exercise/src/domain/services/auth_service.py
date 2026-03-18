"""Authentication service - business logic for user registration and login."""

from datetime import timedelta
from uuid import uuid4

from src.core.config import get_settings
from src.core.security import create_access_token, hash_password, verify_password
from src.domain.entities.user import User
from src.domain.repositories.user_repository import UserRepository
from src.schemas.token_schemas import Token
from src.schemas.user_schemas import UserCreate


class AuthService:
    """
    Authentication service.

    Handles: user registration, login, token creation.

    Depends on UserRepository interface — NOT the database directly.
    This makes it easy to test with a mock repository.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_data: Validated registration data (username, email, password)

        Returns:
            User: Created user entity (without plain password)

        Raises:
            ValueError: If username or email is already taken
        """
        # Check for duplicate username
        if self.user_repository.get_by_username(user_data.username):
            raise ValueError("Username already registered")

        # Check for duplicate email
        if self.user_repository.get_by_email(str(user_data.email)):
            raise ValueError("Email already registered")

        # Build domain entity with hashed password
        user = User(
            id=uuid4().int,
            username=user_data.username,
            email=str(user_data.email),
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
        )

        return self.user_repository.create(user)

    def authenticate_user(self, username: str, password: str) -> User | None:
        """
        Authenticate a user with username and password.

        Args:
            username: Username to look up
            password: Plain text password to verify

        Returns:
            User if credentials are valid and account is active, None otherwise
        """
        user = self.user_repository.get_by_username(username)

        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None

        return user

    def create_token(self, user: User) -> Token:
        """
        Create a JWT access token for an authenticated user.

        Args:
            user: Authenticated user entity

        Returns:
            Token: Access token + token type
        """
        settings = get_settings()
        expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=expires,
        )
        return Token(access_token=access_token, token_type="bearer")
