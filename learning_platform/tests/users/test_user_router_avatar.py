import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock, AsyncMock
from src.core.schemas import PresignedUrlResponse
from src.users.models import User

@pytest.mark.asyncio
async def test_request_avatar_presigned_url(client: AsyncClient, auth_headers):
    # Patch storage_service dependency
    from src.main import app
    from src.core.dependencies import get_storage_service
    
    mock_storage = AsyncMock()
    mock_storage.generate_presigned_put.return_value = PresignedUrlResponse(
        upload_url="https://s3.amazonaws.com/upload",
        object_key="avatars/test.jpg",
        expires_in=300
    )
    
    app.dependency_overrides[get_storage_service] = lambda: mock_storage
    
    try:
        resp = await client.post(
            "/api/v1/users/me/avatar/presigned",
            headers=auth_headers,
            json={"content_type": "image/jpeg", "file_size_bytes": 1024, "file_name": "test.jpg"}
        )
        assert resp.status_code == 201
        assert resp.json()["upload_url"] == "https://s3.amazonaws.com/upload"
    finally:
        app.dependency_overrides.pop(get_storage_service)

@pytest.mark.asyncio
async def test_confirm_avatar_upload(client: AsyncClient, auth_headers):
    from src.main import app
    from src.core.dependencies import get_storage_service
    from src.users.dependencies import get_user_service
    
    mock_storage = AsyncMock()
    mock_storage.validate_and_get_avatar_url.return_value = "https://cdn.example.com/avatar.jpg"
    
    mock_user_service = AsyncMock()
    mock_user = MagicMock(spec=User)
    mock_user.id = "00000000-0000-0000-0000-000000000123"
    mock_user.email = "test@example.com"
    mock_user.role = "student"
    mock_user.display_name = "Test User"
    mock_user.avatar = "https://cdn.example.com/avatar.jpg"
    # To pass UserResponse validation
    mock_user.created_at = "2023-01-01T00:00:00"
    
    mock_user_service.update_avatar.return_value = mock_user
    
    app.dependency_overrides[get_storage_service] = lambda: mock_storage
    app.dependency_overrides[get_user_service] = lambda: mock_user_service
    
    try:
        resp = await client.patch(
            "/api/v1/users/me/avatar",
            headers=auth_headers,
            json={"object_key": "avatars/123/test.jpg"}
        )
        assert resp.status_code == 200
        assert resp.json()["avatar"] == "https://cdn.example.com/avatar.jpg"
    finally:
        app.dependency_overrides.pop(get_storage_service)
        app.dependency_overrides.pop(get_user_service)
