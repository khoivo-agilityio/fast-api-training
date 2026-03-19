"""User repository interface (abstract base class).

This module defines the contract for user data access operations.
The actual implementation will be in the infrastructure layer.
"""

from abc import ABC, abstractmethod

from src.domain.entities.user import User


class UserRepository(ABC):
    """
    Abstract repository for User entity.

    This is an INTERFACE - it defines the contract for user data access.
    Any class that implements this interface must provide all these methods.

    Benefits:
    - Separates domain logic from infrastructure concerns
    - Makes it easy to swap database implementations
    - Enables better testing with mock repositories
    - Follows Dependency Inversion Principle (SOLID)
    """

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user.

        Args:
            user: User entity to create

        Returns:
            User: Created user with ID assigned

        Raises:
            ValueError: If user already exists
        """
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID.

        Args:
            user_id: User ID to search for

        Returns:
            User | None: User if found, None otherwise
        """
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> User | None:
        """Get user by username.

        Args:
            username: Username to search for

        Returns:
            User | None: User if found, None otherwise
        """
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: Email to search for

        Returns:
            User | None: User if found, None otherwise
        """
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update existing user.

        Args:
            user: User entity with updated data

        Returns:
            User: Updated user entity

        Raises:
            ValueError: If user not found
        """
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete user by ID.

        Args:
            user_id: ID of user to delete

        Returns:
            bool: True if deleted, False if not found
        """
        pass
