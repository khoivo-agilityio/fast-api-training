import pytest
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from src.users.management.create_admin import create_admin, main
from src.users.models import UserRole

@pytest.mark.asyncio
async def test_create_admin_success():
    with patch("src.users.management.create_admin.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value = AsyncMock()
        mock_session = mock_session_factory.return_value.__aenter__.return_value
        mock_session.commit = AsyncMock()
        
        with patch("src.users.management.create_admin.UserService") as mock_user_service_cls:
            mock_service = MagicMock()
            mock_user_service_cls.return_value = mock_service
            mock_service.get_by_email = AsyncMock(return_value=None)
            
            with patch("src.users.management.create_admin.hash_password") as mock_hash:
                mock_hash = AsyncMock(return_value="hashed")
                # patch hash_password directly instead of its return value
                with patch("src.users.management.create_admin.hash_password", mock_hash):
                    await create_admin("admin@example.com", "password123", "Admin")
                
                mock_session.add.assert_called_once()
                added_user = mock_session.add.call_args[0][0]
                assert added_user.email == "admin@example.com"
                assert added_user.password == "hashed"
                assert added_user.display_name == "Admin"
                assert added_user.role == UserRole.ADMIN
                mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_create_admin_already_exists_admin():
    with patch("src.users.management.create_admin.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value = AsyncMock()
        mock_session = mock_session_factory.return_value.__aenter__.return_value
        mock_session.commit = AsyncMock()
        
        with patch("src.users.management.create_admin.UserService") as mock_user_service_cls:
            mock_service = MagicMock()
            mock_user_service_cls.return_value = mock_service
            
            existing_user = MagicMock()
            existing_user.role = UserRole.ADMIN
            mock_service.get_by_email = AsyncMock(return_value=existing_user)
            
            await create_admin("admin@example.com", "password123", "Admin")
            
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_create_admin_already_exists_other_role():
    with patch("src.users.management.create_admin.async_session_factory") as mock_session_factory:
        mock_session_factory.return_value = AsyncMock()
        mock_session = mock_session_factory.return_value.__aenter__.return_value
        mock_session.commit = AsyncMock()
        
        with patch("src.users.management.create_admin.UserService") as mock_user_service_cls:
            mock_service = MagicMock()
            mock_user_service_cls.return_value = mock_service
            
            existing_user = MagicMock()
            existing_user.role = "student"
            mock_service.get_by_email = AsyncMock(return_value=existing_user)
            
            await create_admin("admin@example.com", "password123", "Admin")
            
            mock_session.add.assert_not_called()
            mock_session.commit.assert_not_called()

def test_main_success():
    test_args = ["create_admin.py", "--email", "admin@example.com", "--password", "password123", "--display-name", "Admin"]
    with patch.object(sys, "argv", test_args):
        with patch("src.users.management.create_admin.asyncio.run") as mock_run:
            main()
            mock_run.assert_called_once()

def test_main_password_too_short():
    test_args = ["create_admin.py", "--email", "admin@example.com", "--password", "short"]
    with patch.object(sys, "argv", test_args):
        with patch("src.users.management.create_admin.sys.exit") as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                main()
            mock_exit.assert_called_once_with(1)
