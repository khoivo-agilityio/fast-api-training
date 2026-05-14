"""
Tests for StorageService — mocks aioboto3 to avoid real S3 calls.

Mock strategy:
  - Patch get_s3_session() to return a mock session
  - The session.client() is an async context manager returning a mock s3 client
  - All s3.method() calls are AsyncMock

Magic-bytes tests are also included here since the logic now lives in service.py.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import StorageObjectNotFound, UnsupportedFileType
from src.core.service import StorageService, _detect_content_type

# Magic byte fixtures
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 12  # JFIF JPEG
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
GIF87_HEADER = b"GIF87a" + b"\x00" * 6
GIF89_HEADER = b"GIF89a" + b"\x00" * 6
WEBP_HEADER = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP"  # 12 bytes exactly
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
# _detect_content_type (magic bytes)
# ---------------------------------------------------------------------------


class TestDetectContentType:
    """Happy-path: correct magic bytes return the right MIME type."""

    def test_jpeg_detected(self):
        assert _detect_content_type(JPEG_HEADER) == "image/jpeg"

    def test_png_detected(self):
        assert _detect_content_type(PNG_HEADER) == "image/png"

    def test_gif87_detected(self):
        assert _detect_content_type(GIF87_HEADER) == "image/gif"

    def test_gif89_detected(self):
        assert _detect_content_type(GIF89_HEADER) == "image/gif"

    def test_webp_detected(self):
        assert _detect_content_type(WEBP_HEADER) == "image/webp"


class TestDetectContentTypeRejects:
    """Unsupported or spoofed bytes raise UnsupportedFileType."""

    def test_pdf_bytes_rejected(self):
        with pytest.raises(UnsupportedFileType):
            _detect_content_type(b"%PDF-1.4" + b"\x00" * 4)

    def test_zip_bytes_rejected(self):
        with pytest.raises(UnsupportedFileType):
            _detect_content_type(b"PK\x03\x04" + b"\x00" * 8)

    def test_plain_text_rejected(self):
        with pytest.raises(UnsupportedFileType):
            _detect_content_type(b"Hello, world!" + b"\x00" * 3)

    def test_empty_bytes_rejected(self):
        with pytest.raises(UnsupportedFileType):
            _detect_content_type(b"")

    def test_riff_non_webp_rejected(self):
        """RIFF container that is NOT WebP (e.g. AVI) must be rejected."""
        bad = b"RIFF" + b"\x00\x00\x00\x00" + b"AVI "
        with pytest.raises(UnsupportedFileType):
            _detect_content_type(bad)

    def test_fake_jpeg_prefix_rejected(self):
        """Only first 3 bytes match JPEG — still valid (JPEG only needs FF D8 FF)."""
        # This is actually valid JPEG — confirms we don't over-reject
        assert _detect_content_type(b"\xff\xd8\xff" + b"\x00" * 9) == "image/jpeg"

    def test_html_disguised_as_image_rejected(self):
        """Content-Type spoofing attempt — HTML bytes not accepted."""
        with pytest.raises(UnsupportedFileType):
            _detect_content_type(b"<html><head>" + b"\x00" * 3)


# ---------------------------------------------------------------------------
# generate_presigned_put
# ---------------------------------------------------------------------------


class TestGeneratePresignedPut:
    async def test_returns_presigned_response_for_jpeg(self):
        mock_s3, mock_session = _make_s3_mock(presigned_url="https://minio/signed")

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            result = await svc.generate_presigned_put("image/jpeg")

        assert result.upload_url == "https://minio/signed"
        assert result.object_key.startswith("avatars/")
        assert result.object_key.endswith(".jpg")
        assert result.expires_in > 0

    async def test_returns_png_extension_for_png(self):
        _, mock_session = _make_s3_mock()

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            result = await svc.generate_presigned_put("image/png")

        assert result.object_key.endswith(".png")

    async def test_raises_for_unsupported_content_type(self):
        _, mock_session = _make_s3_mock()

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.generate_presigned_put("application/pdf")

    async def test_raises_for_video_content_type(self):
        """Videos are not in the allow-list (images only)."""
        _, mock_session = _make_s3_mock()

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.generate_presigned_put("video/mp4")

    async def test_no_s3_call_on_unsupported_type(self):
        """S3 should NOT be called if the content_type is invalid."""
        mock_s3, mock_session = _make_s3_mock()

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.generate_presigned_put("text/html")

        mock_s3.generate_presigned_url.assert_not_called()

    async def test_custom_folder_used_in_key(self):
        _, mock_session = _make_s3_mock()

        with patch("src.core.service.get_s3_session", return_value=mock_session):
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
        monkeypatch.setattr(
            "src.core.service.settings.MINIO_PUBLIC_ENDPOINT_URL", "http://localhost:9000"
        )
        monkeypatch.setattr("src.core.service.settings.MINIO_BUCKET", "learning-platform")

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            url = await svc.validate_and_get_avatar_url("avatars/abc.jpg")

        assert url == "http://localhost:9000/learning-platform/avatars/abc.jpg"
        mock_s3.delete_object.assert_not_called()

    async def test_invalid_bytes_raises_and_deletes_object(self):
        mock_s3, mock_session = _make_s3_mock(body_bytes=GARBAGE_BYTES)

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(UnsupportedFileType):
                await svc.validate_and_get_avatar_url("avatars/bad.jpg")

        # Object must be cleaned up from S3
        mock_s3.delete_object.assert_called_once()

    async def test_missing_object_raises_storage_not_found(self):
        from botocore.exceptions import ClientError

        error = ClientError({"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject")
        mock_s3, mock_session = _make_s3_mock(get_object_error=error)

        with patch("src.core.service.get_s3_session", return_value=mock_session):
            svc = StorageService()
            with pytest.raises(StorageObjectNotFound):
                await svc.validate_and_get_avatar_url("avatars/missing.jpg")
