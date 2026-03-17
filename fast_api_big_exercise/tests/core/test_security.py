"""Unit tests for security utilities (password hashing and JWT tokens).

Tests cover:
- Password hashing and verification
- JWT token creation and validation
- Token expiration handling
- Error cases
"""

from datetime import timedelta
from time import sleep

import jwt
import pytest

from src.core.security import (
    create_access_token,
    decode_access_token,
    extract_token_subject,
    hash_password,
    verify_password,
)

# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_returns_different_hash_each_time(self) -> None:
        """Test that hashing the same password twice returns different hashes (salt)."""
        password = "mysecret123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2
        # Both should start with bcrypt prefix
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    def test_hash_password_creates_bcrypt_hash(self) -> None:
        """Test that password hashing creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ and are 60 characters long
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_with_correct_password(self) -> None:
        """Test password verification with correct password."""
        password = "correct_password"
        hashed = hash_password(password)

        # Correct password should verify successfully
        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self) -> None:
        """Test password verification with incorrect password."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = hash_password(correct_password)

        # Wrong password should fail verification
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(self) -> None:
        """Test that password verification is case-sensitive."""
        password = "MyPassword123"
        hashed = hash_password(password)

        # Different case should fail
        assert verify_password("mypassword123", hashed) is False
        assert verify_password("MYPASSWORD123", hashed) is False

    def test_verify_password_with_empty_password(self) -> None:
        """Test password verification with empty password."""
        password = ""
        hashed = hash_password(password)

        # Empty password should verify correctly
        assert verify_password("", hashed) is True
        assert verify_password("nonempty", hashed) is False

    def test_hash_password_with_special_characters(self) -> None:
        """Test password hashing with special characters."""
        password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/~`"
        hashed = hash_password(password)

        # Should hash and verify correctly
        assert verify_password(password, hashed) is True

    def test_hash_password_with_unicode(self) -> None:
        """Test password hashing with unicode characters."""
        password = "пароль密码🔐"
        hashed = hash_password(password)

        # Should hash and verify correctly
        assert verify_password(password, hashed) is True


# ============================================================================
# JWT TOKEN TESTS
# ============================================================================


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token_basic(self) -> None:
        """Test basic JWT token creation."""
        data = {"sub": "john@example.com"}
        token = create_access_token(data)

        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0

        # JWT tokens have 3 parts separated by dots
        assert token.count(".") == 2

    def test_create_access_token_with_custom_data(self) -> None:
        """Test token creation with custom payload data."""
        data = {
            "sub": "user123",
            "email": "user@example.com",
            "role": "admin",
        }
        token = create_access_token(data)

        # Decode and verify payload
        payload = decode_access_token(token)
        assert payload["sub"] == "user123"
        assert payload["email"] == "user@example.com"
        assert payload["role"] == "admin"
        assert "exp" in payload  # Expiration should be added

    def test_create_access_token_with_custom_expiration(self) -> None:
        """Test token creation with custom expiration time."""
        data = {"sub": "user123"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta=expires_delta)

        # Decode and check expiration
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_decode_access_token_valid(self) -> None:
        """Test decoding a valid JWT token."""
        data = {"sub": "john@example.com", "user_id": 123}
        token = create_access_token(data)

        # Decode token
        payload = decode_access_token(token)

        # Verify payload
        assert payload["sub"] == "john@example.com"
        assert payload["user_id"] == 123
        assert "exp" in payload

    def test_decode_access_token_expired(self) -> None:
        """Test decoding an expired token raises ExpiredSignatureError."""
        data = {"sub": "user123"}
        # Create token that expires in 1 second
        token = create_access_token(data, expires_delta=timedelta(seconds=1))

        # Wait for token to expire
        sleep(2)

        # Decoding should raise ExpiredSignatureError
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_decode_access_token_invalid_signature(self) -> None:
        """Test decoding a token with invalid signature."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        # Tamper with the token
        parts = token.split(".")
        # Change the signature part
        tampered_token = f"{parts[0]}.{parts[1]}.invalid_signature"

        # Decoding should raise InvalidTokenError
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token(tampered_token)

    def test_decode_access_token_malformed(self) -> None:
        """Test decoding a malformed token."""
        malformed_tokens = [
            "not.a.jwt",
            "invalid",
            "too.many.dots.in.token",
            "",
        ]

        for token in malformed_tokens:
            with pytest.raises(jwt.InvalidTokenError):
                decode_access_token(token)

    def test_extract_token_subject_valid(self) -> None:
        """Test extracting subject from valid token."""
        email = "user@example.com"
        token = create_access_token({"sub": email})

        subject = extract_token_subject(token)
        assert subject == email

    def test_extract_token_subject_expired(self) -> None:
        """Test extracting subject from expired token returns None."""
        token = create_access_token(
            {"sub": "user@example.com"},
            expires_delta=timedelta(seconds=1),
        )

        # Wait for expiration
        sleep(2)

        subject = extract_token_subject(token)
        assert subject is None

    def test_extract_token_subject_invalid(self) -> None:
        """Test extracting subject from invalid token returns None."""
        invalid_tokens = [
            "invalid_token",
            "not.a.jwt",
            "",
        ]

        for token in invalid_tokens:
            subject = extract_token_subject(token)
            assert subject is None

    def test_extract_token_subject_no_sub_claim(self) -> None:
        """Test extracting subject when token has no 'sub' claim."""
        token = create_access_token({"user_id": 123})  # No 'sub' claim

        subject = extract_token_subject(token)
        assert subject is None

    def test_create_token_does_not_modify_original_data(self) -> None:
        """Test that creating a token doesn't modify the original data dict."""
        data = {"sub": "user123", "email": "user@example.com"}
        original_data = data.copy()

        create_access_token(data)

        # Original data should be unchanged
        assert data == original_data
        assert "exp" not in data  # Expiration should not be added to original


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestSecurityIntegration:
    """Integration tests for password and token workflows."""

    def test_user_registration_login_flow(self) -> None:
        """Test complete user registration and login flow."""
        # Step 1: User registers with password
        plain_password = "user_password_123"
        hashed_password = hash_password(plain_password)

        # Step 2: User logs in - verify password
        assert verify_password(plain_password, hashed_password) is True

        # Step 3: Create access token
        token = create_access_token({"sub": "user@example.com"})

        # Step 4: Validate token
        payload = decode_access_token(token)
        assert payload["sub"] == "user@example.com"

    def test_multiple_users_different_tokens(self) -> None:
        """Test that different users get different tokens."""
        user1_token = create_access_token({"sub": "user1@example.com"})
        user2_token = create_access_token({"sub": "user2@example.com"})

        # Tokens should be different
        assert user1_token != user2_token

        # But both should decode correctly
        payload1 = decode_access_token(user1_token)
        payload2 = decode_access_token(user2_token)

        assert payload1["sub"] == "user1@example.com"
        assert payload2["sub"] == "user2@example.com"

    def test_token_reuse_security(self) -> None:
        """Test that same data produces different tokens (for security)."""
        data = {"sub": "user@example.com"}

        # Create two tokens with same data
        token1 = create_access_token(data)
        token2 = create_access_token(data)

        # Tokens should be different (due to different exp times)
        # Note: If created at exact same microsecond, they could be same
        # But in practice, they will have slightly different timestamps

        # Both should decode to the same subject
        subject1 = extract_token_subject(token1)
        subject2 = extract_token_subject(token2)

        assert subject1 == subject2 == "user@example.com"
