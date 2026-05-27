import pytest
import jwt as pyjwt
from unittest.mock import AsyncMock, patch

from src.auth.dependencies import get_current_user, require_roles
from src.auth.exceptions import TokenExpired, TokenInvalid, TokenRevoked, InsufficientPermissions
from src.auth.models import BlacklistedToken
from src.users.models import User

class TestDependencies:

    @pytest.mark.asyncio
    @patch("src.auth.jwt.decode_token")
    async def test_get_current_user_success(self, mock_decode, async_session):
        from uuid import uuid4
        user_id = str(uuid4())
        mock_decode.return_value = {"type": "access", "sub": user_id, "role": "admin"}
        user = await get_current_user("token", async_session)
        assert str(user.id) == user_id
        assert user.role == "admin"

    @pytest.mark.asyncio
    @patch("src.auth.jwt.decode_token")
    async def test_get_current_user_expired(self, mock_decode, async_session):
        mock_decode.side_effect = pyjwt.ExpiredSignatureError()
        with pytest.raises(TokenExpired):
            await get_current_user("token", async_session)

    @pytest.mark.asyncio
    @patch("src.auth.jwt.decode_token")
    async def test_get_current_user_invalid(self, mock_decode, async_session):
        mock_decode.side_effect = pyjwt.InvalidTokenError()
        with pytest.raises(TokenInvalid):
            await get_current_user("token", async_session)

    @pytest.mark.asyncio
    @patch("src.auth.jwt.decode_token")
    async def test_get_current_user_wrong_type(self, mock_decode, async_session):
        mock_decode.return_value = {"type": "refresh", "sub": "some-id"}
        with pytest.raises(TokenInvalid):
            await get_current_user("token", async_session)

    @pytest.mark.asyncio
    @patch("src.auth.jwt.decode_token")
    async def test_get_current_user_no_sub(self, mock_decode, async_session):
        mock_decode.return_value = {"type": "access"}
        with pytest.raises(TokenInvalid):
            await get_current_user("token", async_session)

    @pytest.mark.asyncio
    @patch("src.auth.jwt.decode_token")
    async def test_get_current_user_revoked(self, mock_decode, async_session):
        from uuid import uuid4
        mock_decode.return_value = {"type": "access", "sub": str(uuid4()), "jti": "my-jti"}
        
        # Add to blacklist
        from datetime import datetime, UTC
        record = BlacklistedToken(jti="my-jti", expires_at=datetime.now(UTC))
        async_session.add(record)
        await async_session.commit()
        
        with pytest.raises(TokenRevoked):
            await get_current_user("token", async_session)

    @pytest.mark.asyncio
    async def test_require_roles_success(self):
        from uuid import uuid4
        user = User(id=uuid4(), role="admin")
        dependency = require_roles("admin", "instructor")
        
        result = await dependency(current_user=user)
        assert result == user

    @pytest.mark.asyncio
    async def test_require_roles_failure(self):
        from uuid import uuid4
        user = User(id=uuid4(), role="student")
        dependency = require_roles("admin", "instructor")
        
        with pytest.raises(InsufficientPermissions):
            await dependency(current_user=user)
