import pytest
from src.users.models import User, UserRole

def test_user_str():
    user = User(email="test@example.com", display_name="Test User")
    assert str(user) == "Test User <test@example.com>"

@pytest.mark.asyncio
async def test_user_repository_list_all(async_session):
    from src.users.repository import UserRepository
    repo = UserRepository(async_session)
    user = User(email="test2@example.com", display_name="Test", password="pwd")
    async_session.add(user)
    await async_session.commit()
    
    users = await repo.list_all()
    assert len(users) >= 1
    assert any(u.email == "test2@example.com" for u in users)

def test_user_schema_avatar_validation():
    from src.users.schemas import UserUpdateRequest
    # Valid
    req = UserUpdateRequest(avatar="https://bucket.s3.amazonaws.com/image.jpg")
    assert req.avatar is not None
    
    # None
    req2 = UserUpdateRequest(avatar=None)
    assert req2.avatar is None
    
    # Invalid
    with pytest.raises(ValueError):
        UserUpdateRequest(avatar="https://example.com/image.jpg")
