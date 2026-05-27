import pytest
import uuid
from src.users.models import User
from src.users.schemas import UserUpdateRequest
from src.users.service import UserService
from unittest.mock import patch, AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_create_user(async_session):
    service = UserService(async_session)
    user = await service.create_user("test@example.com", "password", "Name", "student")
    assert user.email == "test@example.com"
    assert user.display_name == "Name"
    assert user.role == "student"
    assert user.password != "password"  # hashed

@pytest.mark.asyncio
async def test_update_profile_with_password(async_session):
    service = UserService(async_session)
    user = await service.create_user("updatepwd@example.com", "oldpassword", "Name")
    
    req = UserUpdateRequest(password="newpassword")
    updated = await service.update_profile(user.id, req)
    
    from src.auth.security import verify_password
    assert await verify_password("newpassword", updated.password)

@pytest.mark.asyncio
async def test_delete_user(async_session):
    service = UserService(async_session)
    user = await service.create_user("delete@example.com", "password", "Name")
    
    await service.delete(user.id)
    
    # Verify it is deleted
    deleted_user = await service.get_by_email("delete@example.com")
    assert deleted_user is None

@pytest.mark.asyncio
async def test_update_avatar(async_session):
    service = UserService(async_session)
    user = await service.create_user("avatar@example.com", "password", "Name")
    
    updated = await service.update_avatar(user.id, "https://bucket.s3.amazonaws.com/image.jpg")
    assert updated.avatar == "https://bucket.s3.amazonaws.com/image.jpg"
