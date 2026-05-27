import pytest

class TestStorageServiceExtra:
    """Extra tests for missing coverage in StorageService."""

    def test_build_object_url_local(self):
        from src.core.service import StorageService
        from unittest.mock import patch
        
        service = StorageService()
        with patch("src.core.service.settings.STORAGE_BACKEND", "local"):
            url = service._build_object_url("avatars/test.jpg")
            assert "avatars/test.jpg" in url

    def test_build_object_url_aws(self):
        from src.core.service import StorageService
        from unittest.mock import patch
        
        service = StorageService()
        with patch("src.core.service.settings.STORAGE_BACKEND", "s3"):
            url = service._build_object_url("avatars/test.jpg")
            assert "amazonaws.com" in url

    @pytest.mark.asyncio
    async def test_validate_and_get_avatar_url_client_error_other(self):
        from src.core.service import StorageService
        from botocore.exceptions import ClientError
        from unittest.mock import patch, AsyncMock, MagicMock
        
        service = StorageService()
        mock_session = MagicMock()
        mock_s3 = AsyncMock()
        mock_session.client.return_value.__aenter__.return_value = mock_s3
        
        # Simulate a non-404 ClientError
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Forbidden"}}
        mock_s3.get_object.side_effect = ClientError(error_response, "GetObject")
        
        with patch("src.core.service.get_s3_session", return_value=mock_session):
            with pytest.raises(ClientError):
                await service.validate_and_get_avatar_url("test_key")

    @pytest.mark.asyncio
    async def test_delete_object(self):
        from src.core.service import StorageService
        from unittest.mock import patch, AsyncMock, MagicMock
        
        service = StorageService()
        mock_session = MagicMock()
        mock_s3 = AsyncMock()
        mock_session.client.return_value.__aenter__.return_value = mock_s3
        
        with patch("src.core.service.get_s3_session", return_value=mock_session):
            await service.delete_object("test_key")
            mock_s3.delete_object.assert_called_once()
