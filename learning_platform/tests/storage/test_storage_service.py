"""
Tests for StorageService — mocks aioboto3 to avoid real S3 calls.

Mock strategy:
  - Patch get_s3_session() to return a mock session
  - The session.client() is an async context manager returning a mock s3 client
  - All s3.method() calls are AsyncMock
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.storage.exceptions import StorageObjectNotFound, UnsupportedFileType
from src.storage.service import StorageService

# Magic byte fixtures
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 12
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
GARBAGE_BYTES = b"notanimage!!"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_s3_mock(
    presigned_url: str = "https://minio/upload",
    body_bytes: bytes = JPEG_HEADER,
    get_object_error: Exception | None = None,
) -> tuple[AsyncMock, MagicMock]:
    """Build a mock aioboto3 s3 client + session pair."""
    mock_s3 = AsyncMock()
    mock_s3.generate_presigned_url = AsyncMock(return_value=presigned_url)

    if get_object_error:
        mock_s3.get_object = AsyncMock(side_effect=get_object_error)
    else:
        mock_body = AsyncMock()
        mock_body.read = AsyncMock(return_value=body_bytes)
        mock_s3.get_object = AsyncMock(return_value={"Body": mock_body})

    mock_s3.delete_object = AsyncMock(return_value={})

    # Async context manager for session.client(...)
    mock_cm = AsyncMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_s3)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.client.return_value = mock_cm

    return mock_s3, mock_session


# ---------------------------------------------------------------------------
# generate_presigned_put
# ---------------------------------------------------------------------------


class TestGeneratePresignedPut:
    async def test_returns_presigned_response_for_jpeg(self):
        mock_s3, mock_session = _make_s3_mock(presigned_url="https://minio/signed")

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            result = await svc.generate_presigned_put("image/jpeg")

        assert result.upload_url == "https://minio/signed"
        assert result.object_key.startswith("avatars/")
        assert result.object_key.endswith(".jpg")
        assert result.expires_in > 0

    async def test_returns_png_extension_for_png(self):
        _, mock_session = _make_s3_mock()

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            result = await svc.generate_presigned_put("image/png")

        assert result.object_key.endswith(".png")

    async def test_raises_for_unsupported_content_type(self):
        _, mock_session = _make_s3_mock()

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.generate_presigned_put("application/pdf")

    async def test_raises_for_video_content_type(self):
        """Videos are not in the allow-list (images only)."""
        _, mock_session = _make_s3_mock()

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.generate_presigned_put("video/mp4")

    async def test_no_s3_call_on_unsupported_type(self):
        """S3 should NOT be called if the content_type is invalid."""
        mock_s3, mock_session = _make_s3_mock()

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.generate_presigned_put("text/html")

        mock_s3.generate_presigned_url.assert_not_called()

    async def test_custom_folder_used_in_key(self):
        _, mock_session = _make_s3_mock()

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            result = await svc.generate_presigned_put("image/webp", folder="thumbs")

        assert result.object_key.startswith("thumbs/")
        assert result.object_key.endswith(".webp")


# ---------------------------------------------------------------------------
# validate_and_get_avatar_url
# ---------------------------------------------------------------------------


class TestValidateAndGetAvatarUrl:
    async def test_valid_jpeg_returns_url(self, monkeypatch):
        mock_s3, mock_session = _make_s3_mock(body_bytes=JPEG_HEADER)
        monkeypatch.setattr("src.storage.service.settings.CLOUDFRONT_BASE_URL", None)
        monkeypatch.setattr(
            "src.storage.service.settings.S3_PUBLIC_ENDPOINT_URL", "http://localhost:9000"
        )
        monkeypatch.setattr(
            "src.storage.service.settings.S3_BUCKET_NAME", "learning-platform"
        )

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            url = await svc.validate_and_get_avatar_url("avatars/abc.jpg")

        assert url == "http://localhost:9000/learning-platform/avatars/abc.jpg"
        mock_s3.delete_object.assert_not_called()

    async def test_cloudfront_url_returned_when_configured(self, monkeypatch):
        mock_s3, mock_session = _make_s3_mock(body_bytes=PNG_HEADER)
        monkeypatch.setattr(
            "src.storage.service.settings.CLOUDFRONT_BASE_URL", "https://d1.cloudfront.net"
        )

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            url = await svc.validate_and_get_avatar_url("avatars/abc.png")

        assert url == "https://d1.cloudfront.net/avatars/abc.png"

    async def test_invalid_bytes_raises_and_deletes_object(self):
        mock_s3, mock_session = _make_s3_mock(body_bytes=GARBAGE_BYTES)

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.validate_and_get_avatar_url("avatars/bad.jpg")

        # Object must be cleaned up from S3
        mock_s3.delete_object.assert_called_once()

    async def test_missing_object_raises_storage_not_found(self):
        from botocore.exceptions import ClientError

        error = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
        )
        mock_s3, mock_session = _make_s3_mock(get_object_error=error)

        with patch("src.storage.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(StorageObjectNotFound):
                await svc.validate_and_get_avatar_url("avatars/missing.jpg")
