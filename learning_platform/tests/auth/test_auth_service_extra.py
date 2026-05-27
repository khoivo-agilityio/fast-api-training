import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.service import AuthService

class TestAuthServiceRefresh:
    """Tests for AuthService.refresh()."""

    @pytest_asyncio.fixture
    async def service(self, async_session: AsyncSession) -> AuthService:
        return AuthService(async_session)

    @pytest.mark.asyncio
    async def test_refresh_success(self, service: AuthService, async_session):
        from src.auth import jwt
        tokens = jwt.create_token_pair("test-id", "student")
        
        result = await service.refresh(tokens["refresh_token"])
        assert result.access_token
        assert result.refresh_token

    @pytest.mark.asyncio
    async def test_refresh_expired(self, service: AuthService):
        from unittest.mock import patch
        import jwt as pyjwt
        from src.auth.exceptions import TokenExpired
        with patch("src.auth.jwt.decode_token", side_effect=pyjwt.ExpiredSignatureError()):
            with pytest.raises(TokenExpired):
                await service.refresh("some_token")

    @pytest.mark.asyncio
    async def test_refresh_invalid(self, service: AuthService):
        from unittest.mock import patch
        import jwt as pyjwt
        from src.auth.exceptions import TokenInvalid
        with patch("src.auth.jwt.decode_token", side_effect=pyjwt.InvalidTokenError()):
            with pytest.raises(TokenInvalid):
                await service.refresh("some_token")

    @pytest.mark.asyncio
    async def test_refresh_wrong_type(self, service: AuthService):
        from unittest.mock import patch
        from src.auth.exceptions import TokenInvalid
        with patch("src.auth.jwt.decode_token", return_value={"type": "access"}):
            with pytest.raises(TokenInvalid):
                await service.refresh("some_token")

    @pytest.mark.asyncio
    async def test_refresh_no_jti(self, service: AuthService):
        from unittest.mock import patch
        from src.auth.exceptions import TokenInvalid
        with patch("src.auth.jwt.decode_token", return_value={"type": "refresh"}):
            with pytest.raises(TokenInvalid):
                await service.refresh("some_token")

    @pytest.mark.asyncio
    async def test_refresh_revoked(self, service: AuthService, async_session):
        from src.auth import jwt
        from src.auth.exceptions import TokenRevoked
        from src.auth.models import BlacklistedToken
        from datetime import datetime, UTC
        
        tokens = jwt.create_token_pair("test-id", "student")
        payload = jwt.decode_token(tokens["refresh_token"])
        
        record = BlacklistedToken(jti=payload["jti"], expires_at=datetime.now(UTC))
        async_session.add(record)
        await async_session.commit()
        
        with pytest.raises(TokenRevoked):
            await service.refresh(tokens["refresh_token"])


class TestAuthServiceLogout:
    """Tests for AuthService.logout()."""

    @pytest_asyncio.fixture
    async def service(self, async_session: AsyncSession) -> AuthService:
        return AuthService(async_session)

    @pytest.mark.asyncio
    async def test_logout_success(self, service: AuthService, async_session):
        from src.auth import jwt
        tokens = jwt.create_token_pair("test-id", "student")
        
        await service.logout(tokens["access_token"])
        
        # Verify it's blacklisted
        payload = jwt.decode_token(tokens["access_token"])
        is_blacklisted = await service._is_token_blacklisted(payload["jti"])
        assert is_blacklisted is True

    @pytest.mark.asyncio
    async def test_logout_already_expired(self, service: AuthService):
        from unittest.mock import patch
        import jwt as pyjwt
        # Should just return without exception
        with patch("src.auth.jwt.decode_token", side_effect=pyjwt.ExpiredSignatureError()):
            await service.logout("some_token")

    @pytest.mark.asyncio
    async def test_logout_invalid(self, service: AuthService):
        from unittest.mock import patch
        import jwt as pyjwt
        from src.auth.exceptions import TokenInvalid
        with patch("src.auth.jwt.decode_token", side_effect=pyjwt.InvalidTokenError()):
            with pytest.raises(TokenInvalid):
                await service.logout("some_token")
