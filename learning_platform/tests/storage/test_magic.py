"""
Tests for src/storage/magic.py — magic-bytes file type detection.

These tests use real byte sequences, not mocks, to ensure we catch
file-type spoofing correctly.
"""

import pytest

from src.storage.exceptions import UnsupportedFileType
from src.storage.magic import detect_content_type

# ---------------------------------------------------------------------------
# Real magic byte headers
# ---------------------------------------------------------------------------

JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 12   # JFIF JPEG
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
GIF87_HEADER = b"GIF87a" + b"\x00" * 6
GIF89_HEADER = b"GIF89a" + b"\x00" * 6
WEBP_HEADER = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP"  # 12 bytes exactly


class TestDetectContentType:
    """Happy-path: correct magic bytes return the right MIME type."""

    def test_jpeg_detected(self):
        assert detect_content_type(JPEG_HEADER) == "image/jpeg"

    def test_png_detected(self):
        assert detect_content_type(PNG_HEADER) == "image/png"

    def test_gif87_detected(self):
        assert detect_content_type(GIF87_HEADER) == "image/gif"

    def test_gif89_detected(self):
        assert detect_content_type(GIF89_HEADER) == "image/gif"

    def test_webp_detected(self):
        assert detect_content_type(WEBP_HEADER) == "image/webp"


class TestDetectContentTypeRejects:
    """Unsupported or spoofed bytes raise UnsupportedFileType."""

    def test_pdf_bytes_rejected(self):
        with pytest.raises(UnsupportedFileType):
            detect_content_type(b"%PDF-1.4" + b"\x00" * 4)

    def test_zip_bytes_rejected(self):
        with pytest.raises(UnsupportedFileType):
            detect_content_type(b"PK\x03\x04" + b"\x00" * 8)

    def test_plain_text_rejected(self):
        with pytest.raises(UnsupportedFileType):
            detect_content_type(b"Hello, world!" + b"\x00" * 3)

    def test_empty_bytes_rejected(self):
        with pytest.raises(UnsupportedFileType):
            detect_content_type(b"")

    def test_riff_non_webp_rejected(self):
        """RIFF container that is NOT WebP (e.g. AVI) must be rejected."""
        bad = b"RIFF" + b"\x00\x00\x00\x00" + b"AVI "
        with pytest.raises(UnsupportedFileType):
            detect_content_type(bad)

    def test_fake_jpeg_prefix_rejected(self):
        """Only first 3 bytes match JPEG — still valid (JPEG only needs FF D8 FF)."""
        # This is actually valid JPEG — confirms we don't over-reject
        assert detect_content_type(b"\xff\xd8\xff" + b"\x00" * 9) == "image/jpeg"

    def test_html_disguised_as_image_rejected(self):
        """Content-Type spoofing attempt — HTML bytes not accepted."""
        with pytest.raises(UnsupportedFileType):
            detect_content_type(b"<html><head>" + b"\x00" * 3)
