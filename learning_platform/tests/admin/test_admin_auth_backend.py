import pytest
from starlette.requests import Request
from src.admin_view import AdminAuthBackend, UserAdmin
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_admin_auth_login_success():
    backend = AdminAuthBackend("secret")
    
    mock_request = MagicMock(spec=Request)
    mock_request.session = {}
    
    async def mock_form():
        return {"username": "admin@example.com", "password": "password"}
    mock_request.form = mock_form
    
    with patch("src.admin_view.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value = AsyncMock()
        mock_session = mock_session_factory.return_value.__aenter__.return_value
        mock_session.commit = AsyncMock()
        
        with patch("src.admin_view.AuthService") as mock_auth_service_cls:
            mock_service = MagicMock()
            mock_auth_service_cls.return_value = mock_service
            
            mock_tokens = MagicMock()
            mock_tokens.access_token = "access"
            mock_service.login = AsyncMock(return_value=mock_tokens)
            
            with patch("src.admin_view.decode_token") as mock_decode:
                mock_decode.return_value = {"role": "admin", "sub": "123"}
                
                result = await backend.login(mock_request)
                assert result is True
                assert mock_request.session["token"] == "access"
                assert mock_request.session["user_id"] == "123"

@pytest.mark.asyncio
async def test_admin_auth_login_not_admin():
    backend = AdminAuthBackend("secret")
    
    mock_request = MagicMock(spec=Request)
    mock_request.session = {}
    async def mock_form():
        return {"username": "user@example.com", "password": "password"}
    mock_request.form = mock_form
    
    with patch("src.admin_view.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value = AsyncMock()
        mock_session = mock_session_factory.return_value.__aenter__.return_value
        mock_session.commit = AsyncMock()
        
        with patch("src.admin_view.AuthService") as mock_auth_service_cls:
            mock_service = MagicMock()
            mock_auth_service_cls.return_value = mock_service
            
            mock_tokens = MagicMock()
            mock_tokens.access_token = "access"
            mock_service.login = AsyncMock(return_value=mock_tokens)
            
            with patch("src.admin_view.decode_token") as mock_decode:
                mock_decode.return_value = {"role": "student", "sub": "123"}
                
                result = await backend.login(mock_request)
                assert result is False

@pytest.mark.asyncio
async def test_admin_auth_login_exception():
    backend = AdminAuthBackend("secret")
    
    mock_request = MagicMock(spec=Request)
    mock_request.session = {}
    async def mock_form():
        return {"username": "user@example.com", "password": "password"}
    mock_request.form = mock_form
    
    with patch("src.admin_view.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value = AsyncMock()
        mock_session = mock_session_factory.return_value.__aenter__.return_value
        mock_session.commit = AsyncMock()
        
        with patch("src.admin_view.AuthService") as mock_auth_service_cls:
            mock_service = MagicMock()
            mock_auth_service_cls.return_value = mock_service
            mock_service.login = AsyncMock(side_effect=Exception("error"))
            
            result = await backend.login(mock_request)
            assert result is False

@pytest.mark.asyncio
async def test_admin_auth_logout():
    backend = AdminAuthBackend("secret")
    class DummyRequest:
        def __init__(self):
            self.session = {"token": "123"}
    
    dummy_req = DummyRequest()
    result = await backend.logout(dummy_req)
    assert result is True
    assert dummy_req.session == {}

@pytest.mark.asyncio
async def test_admin_auth_authenticate_success():
    backend = AdminAuthBackend("secret")
    mock_request = MagicMock(spec=Request)
    mock_request.session = {"token": "token"}
    
    with patch("src.admin_view.decode_token") as mock_decode:
        mock_decode.return_value = {"role": "admin"}
        result = await backend.authenticate(mock_request)
        assert result is True

@pytest.mark.asyncio
async def test_admin_auth_authenticate_no_token():
    backend = AdminAuthBackend("secret")
    mock_request = MagicMock(spec=Request)
    mock_request.session = {}
    
    result = await backend.authenticate(mock_request)
    assert result is False

@pytest.mark.asyncio
async def test_admin_auth_authenticate_exception():
    backend = AdminAuthBackend("secret")
    mock_request = MagicMock(spec=Request)
    mock_request.session = {"token": "token"}
    
    with patch("src.admin_view.decode_token") as mock_decode:
        mock_decode.side_effect = Exception()
        result = await backend.authenticate(mock_request)
        assert result is False

@pytest.mark.asyncio
async def test_user_admin_on_model_change():
    mock_model = MagicMock()
    mock_request = MagicMock()
    
    data = {"password": "newpassword"}
    with patch("src.admin_view.hash_password") as mock_hash:
        mock_hash.return_value = "hashed"
        # Since it's an instance method, I'll pass a dummy object as self
        dummy_self = MagicMock()
        await UserAdmin.on_model_change(dummy_self, data, mock_model, True, mock_request)
        assert data["password"] == "hashed"
