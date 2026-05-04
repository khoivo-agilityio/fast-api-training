"""
Tests for auth/security.py — async bcrypt hash/verify.

Verifies Issue #2 fix: bcrypt functions are async and non-blocking
(using run_in_executor under the hood).
"""

import asyncio

from src.auth.security import hash_password, verify_password


class TestHashPassword:
    """Tests for hash_password()."""

    async def test_returns_bcrypt_string(self):
        """Hash should start with $2b$ (bcrypt identifier)."""
        hashed = await hash_password("mysecretpassword")
        assert hashed.startswith("$2b$")

    async def test_is_coroutine(self):
        """hash_password should be a coroutine function (async)."""
        assert asyncio.iscoroutinefunction(hash_password)

    async def test_produces_unique_salts(self):
        """Two hashes of the same password should differ (unique salts)."""
        h1 = await hash_password("samepassword")
        h2 = await hash_password("samepassword")
        assert h1 != h2

    async def test_hash_is_string(self):
        """Return value should be a decoded UTF-8 string, not bytes."""
        hashed = await hash_password("testpass")
        assert isinstance(hashed, str)


class TestVerifyPassword:
    """Tests for verify_password()."""

    async def test_correct_password_returns_true(self):
        """Correct password should verify successfully."""
        hashed = await hash_password("correctpassword")
        result = await verify_password("correctpassword", hashed)
        assert result is True

    async def test_wrong_password_returns_false(self):
        """Wrong password should fail verification."""
        hashed = await hash_password("correctpassword")
        result = await verify_password("wrongpassword", hashed)
        assert result is False

    async def test_is_coroutine(self):
        """verify_password should be a coroutine function (async)."""
        assert asyncio.iscoroutinefunction(verify_password)
