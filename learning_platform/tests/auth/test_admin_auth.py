import pytest
from fastapi import Request
from src.auth.admin_auth import require_admin_or_session
from src.auth.exceptions import InsufficientPermissions
from src.auth import jwt
from unittest.mock import MagicMock

class TestRequireAdminOrSession:

    @pytest.mark.asyncio
    async def test_valid_jwt_bearer(self, async_session):
        token_pair = jwt.create_token_pair("some-id", "admin")
        
        scope = {
            "type": "http",
            "headers": [
                (b"authorization", f"Bearer {token_pair['access_token']}".encode())
            ]
        }
        request = Request(scope)
        # Should not raise
        await require_admin_or_session(request, async_session)

    @pytest.mark.asyncio
    async def test_valid_session_cookie(self, async_session):
        token_pair = jwt.create_token_pair("some-id", "admin")
        
        scope = {
            "type": "http",
            "headers": [],
            "session": {"token": token_pair["access_token"]}
        }
        request = Request(scope)
        # Should not raise
        await require_admin_or_session(request, async_session)

    @pytest.mark.asyncio
    async def test_invalid_jwt_bearer_falls_through_to_session(self, async_session):
        token_pair = jwt.create_token_pair("some-id", "admin")
        
        scope = {
            "type": "http",
            "headers": [
                (b"authorization", b"Bearer invalid.token.here")
            ],
            "session": {"token": token_pair["access_token"]}
        }
        request = Request(scope)
        # Should not raise (falls through to session and succeeds)
        await require_admin_or_session(request, async_session)

    @pytest.mark.asyncio
    async def test_no_auth_raises(self, async_session):
        scope = {
            "type": "http",
            "headers": [],
            "session": {}
        }
        request = Request(scope)
        with pytest.raises(InsufficientPermissions):
            await require_admin_or_session(request, async_session)

    @pytest.mark.asyncio
    async def test_jwt_wrong_role_raises(self, async_session):
        token_pair = jwt.create_token_pair("some-id", "student")
        
        scope = {
            "type": "http",
            "headers": [
                (b"authorization", f"Bearer {token_pair['access_token']}".encode())
            ],
            "session": {}
        }
        request = Request(scope)
        with pytest.raises(InsufficientPermissions):
            await require_admin_or_session(request, async_session)

    @pytest.mark.asyncio
    async def test_jwt_wrong_type_raises(self, async_session):
        token_pair = jwt.create_token_pair("some-id", "admin")
        
        scope = {
            "type": "http",
            "headers": [
                (b"authorization", f"Bearer {token_pair['refresh_token']}".encode())
            ],
            "session": {}
        }
        request = Request(scope)
        with pytest.raises(InsufficientPermissions):
            await require_admin_or_session(request, async_session)

    @pytest.mark.asyncio
    async def test_session_wrong_role_raises(self, async_session):
        token_pair = jwt.create_token_pair("some-id", "student")
        
        scope = {
            "type": "http",
            "headers": [],
            "session": {"token": token_pair["access_token"]}
        }
        request = Request(scope)
        with pytest.raises(InsufficientPermissions):
            await require_admin_or_session(request, async_session)

    @pytest.mark.asyncio
    async def test_session_invalid_token_raises(self, async_session):
        scope = {
            "type": "http",
            "headers": [],
            "session": {"token": "invalid.token.here"}
        }
        request = Request(scope)
        with pytest.raises(InsufficientPermissions):
            await require_admin_or_session(request, async_session)
