"""
Magic-bytes validation for uploaded files.

Never trust the Content-Type header — always validate by inspecting
the first bytes of the actual file content.

Reference magic bytes:
  JPEG  : FF D8 FF
  PNG   : 89 50 4E 47 0D 0A 1A 0A
  GIF   : 47 49 46 38 (GIF8)
  WebP  : 52 49 46 46 ?? ?? ?? ?? 57 45 42 50  (RIFF....WEBP)
"""

from src.storage.exceptions import UnsupportedFileType

# Minimum bytes required for detection (WebP needs 12)
MIN_HEADER_BYTES = 12

# Allowed MIME → file extension mapping
ALLOWED_EXTENSIONS: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}


def detect_content_type(header_bytes: bytes) -> str:
    """Detect MIME type from magic bytes.

    Args:
        header_bytes: First bytes of the file (minimum 12 bytes).

    Returns:
        MIME type string e.g. ``"image/jpeg"``.

    Raises:
        UnsupportedFileType: If the bytes don't match any allowed type.
    """
    if header_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"

    if header_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"

    if header_bytes[:4] == b"GIF8":
        return "image/gif"

    # WebP: bytes 0-3 == RIFF, bytes 8-11 == WEBP
    if header_bytes[:4] == b"RIFF" and header_bytes[8:12] == b"WEBP":
        return "image/webp"

    raise UnsupportedFileType()
