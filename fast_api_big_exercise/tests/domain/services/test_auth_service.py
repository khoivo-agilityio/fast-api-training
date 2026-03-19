"""Unit tests for AuthService.

Uses mock repositories so tests are fast and don't touch the database.
Tests cover:
- register_user (success, duplicate username, duplicate email)
- authenticate_user (success, wrong password, inactive user, not found)
- create_token (token structure and type)
"""

from unittest.mock import MagicMock

import pytest

from src.domain.services.auth_service import AuthService
from src.schemas.user_schemas import UserCreate
from tests.base import BaseUnitTestCase


# ============================================================================
# REGISTER TESTS
# ============================================================================
class TestRegisterUser(BaseUnitTestCase):
    """Tests for AuthService.register_user."""

    def test_register_success(self, auth_service: AuthService, mock_user_repo: MagicMock) -> None:
        """Happy path: new username + email creates a user."""
        user_data = UserCreate(
            username="alice",
            email="alice@example.com",
            password="secret123",
            full_name="Alice",
        )
        result = auth_service.register_user(user_data)

        assert result.username == "alice"
        assert result.email == "alice@example.com"
        assert result.full_name == "Alice"
        assert result.is_active is True
        assert result.hashed_password != "secret123"
        assert result.hashed_password.startswith("$2b$")
        mock_user_repo.create.assert_called_once()

    def test_register_duplicate_username_raises(
        self, auth_service: AuthService, mock_user_repo: MagicMock
    ) -> None:
        """Duplicate username raises ValueError."""
        mock_user_repo.get_by_username.return_value = self.make_user()
        user_data = UserCreate(username="alice", email="new@example.com", password="secret123")
        with pytest.raises(ValueError, match="Username already registered"):
            auth_service.register_user(user_data)
        mock_user_repo.create.assert_not_called()

    def test_register_duplicate_email_raises(
        self, auth_service: AuthService, mock_user_repo: MagicMock
    ) -> None:
        """Duplicate email raises ValueError."""
        mock_user_repo.get_by_username.return_value = None
        mock_user_repo.get_by_email.return_value = self.make_user()
        user_data = UserCreate(username="newuser", email="alice@example.com", password="secret123")
        with pytest.raises(ValueError, match="Email already registered"):
            auth_service.register_user(user_data)
        mock_user_repo.create.assert_not_called()

    def test_register_no_full_name(
        self, auth_service: AuthService, mock_user_repo: MagicMock
    ) -> None:
        """full_name is optional."""
        user_data = UserCreate(username="bob", email="bob@example.com", password="pass1234")
        result = auth_service.register_user(user_data)
        assert result.full_name is None


# ============================================================================
# AUTHENTICATE TESTS
# ============================================================================
class TestAuthenticateUser(BaseUnitTestCase):
    """Tests for AuthService.authenticate_user."""

    def test_authenticate_success(
        self, auth_service: AuthService, mock_user_repo: MagicMock
    ) -> None:
        """Correct credentials return the User entity."""
        mock_user_repo.get_by_username.return_value = self.make_user()
        result = auth_service.authenticate_user("alice", "secret123")
        assert result is not None
        assert result.username == "alice"

    def test_authenticate_wrong_password(
        self, auth_service: AuthService, mock_user_repo: MagicMock
    ) -> None:
        """Wrong password returns None."""
        mock_user_repo.get_by_username.return_value = self.make_user()
        result = auth_service.authenticate_user("alice", "wrongpassword")
        assert result is None

    def test_authenticate_user_not_found(
        self, auth_service: AuthService, mock_user_repo: MagicMock
    ) -> None:
        """Unknown username returns None."""
        mock_user_repo.get_by_username.return_value = None
        result = auth_service.authenticate_user("ghost", "secret123")
        assert result is None

    def test_authenticate_inactive_user(
        self, auth_service: AuthService, mock_user_repo: MagicMock
    ) -> None:
        """Inactive user account returns None even with correct credentials."""
        mock_user_repo.get_by_username.return_value = self.make_user(is_active=False)
        result = auth_service.authenticate_user("alice", "secret123")
        assert result is None


# ============================================================================
# CREATE TOKEN TESTS
# ============================================================================
class TestCreateToken(BaseUnitTestCase):
    """Tests for AuthService.create_token."""

    def test_create_token_returns_bearer(self, auth_service: AuthService) -> None:
        """Token has the correct structure and token_type."""
        token = auth_service.create_token(self.make_user())
        assert token.token_type == "bearer"
        assert len(token.access_token) > 0
        assert len(token.access_token.split(".")) == 3

    def test_create_token_encodes_username(self, auth_service: AuthService) -> None:
        """The token subject should be the user's username."""
        from src.core.security import extract_token_subject

        token = auth_service.create_token(self.make_user(username="charlie"))
        assert extract_token_subject(token.access_token) == "charlie"

    def test_different_users_get_different_tokens(self, auth_service: AuthService) -> None:
        """Two different users get different tokens."""
        token1 = auth_service.create_token(self.make_user(id=1, username="user1"))
        token2 = auth_service.create_token(self.make_user(id=2, username="user2"))
        assert token1.access_token != token2.access_token
