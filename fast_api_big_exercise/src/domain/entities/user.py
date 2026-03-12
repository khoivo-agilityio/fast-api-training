"""User domain entity - pure Python business object."""

from datetime import datetime


class User:
    """
    User domain entity (pure Python, no database dependencies).

    Represents a user in the business domain.
    This is a rich domain model with business logic.
    """

    def __init__(
        self,
        username: str,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        is_active: bool = True,
        id: int | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """
        Initialize a User entity.

        Args:
            username: Unique username (3-50 chars)
            email: User's email address
            hashed_password: Bcrypt hashed password
            full_name: User's full name (optional)
            is_active: Whether user account is active
            id: User ID (None for new users)
            created_at: Account creation timestamp (None = now)
        """
        self.id = id
        self.username = username
        self.email = email
        self.hashed_password = hashed_password
        self.full_name = full_name
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()

    def deactivate(self) -> None:
        """
        Deactivate user account.

        Business rule: Deactivated users cannot log in.
        """
        self.is_active = False

    def activate(self) -> None:
        """
        Activate user account.

        Business rule: Only active users can log in.
        """
        self.is_active = True

    def update_email(self, new_email: str) -> None:
        """
        Update user's email address.

        Args:
            new_email: New email address

        Business rule: Email must be unique (validated by repository).
        """
        self.email = new_email

    def update_full_name(self, new_full_name: str | None) -> None:
        """
        Update user's full name.

        Args:
            new_full_name: New full name (can be None to clear)
        """
        self.full_name = new_full_name

    def update_password(self, new_hashed_password: str) -> None:
        """
        Update user's password.

        Args:
            new_hashed_password: New bcrypt hashed password

        Note: Password should already be hashed by security utilities.
        """
        self.hashed_password = new_hashed_password

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<User(id={self.id}, username='{self.username}', active={self.is_active})>"

    def __eq__(self, other: object) -> bool:
        """
        Compare users by ID.

        Two users are equal if they have the same ID.
        """
        if not isinstance(other, User):
            return False
        return self.id == other.id if self.id is not None else False

    def __hash__(self) -> int:
        """Hash user by ID for use in sets/dicts."""
        return hash(self.id) if self.id is not None else hash(id(self))
