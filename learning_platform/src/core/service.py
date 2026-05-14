"""
Storage Service — S3/MinIO presigned URL generation and object validation.

Magic-bytes validation:
  Never trust the Content-Type header — always validate by inspecting
  the first bytes of the actual file content.

  Reference magic bytes:
    JPEG  : FF D8 FF
    PNG   : 89 50 4E 47 0D 0A 1A 0A
    GIF   : 47 49 46 38 (GIF8)
    WebP  : 52 49 46 46 ?? ?? ?? ?? 57 45 42 50  (RIFF....WEBP)

Flow:
  1. generate_presigned_put()  →  server signs a PUT URL  →  client uploads
  2. validate_and_get_avatar_url()  →  server reads 16 header bytes from S3
                                    →  validates magic bytes
                                    →  returns public S3/MinIO URL

Backend selection (STORAGE_BACKEND env var):
  "local"  →  uses MINIO_* vars, presigns against MINIO_PUBLIC_ENDPOINT_URL
  "s3"     →  uses AWS_* vars, presigns against AWS global endpoint
"""

import uuid

from botocore.exceptions import ClientError

from src.config import settings
from src.core.client import get_boto_config, get_s3_session
from src.core.exceptions import StorageObjectNotFound, UnsupportedFileType
from src.core.schemas import PresignedUrlResponse

# ---------------------------------------------------------------------------
# Magic-bytes constants
# ---------------------------------------------------------------------------

# Minimum bytes required for detection (WebP needs 12)
_MIN_HEADER_BYTES = 12

# Allowed MIME → file extension mapping
ALLOWED_EXTENSIONS: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
}


def _detect_content_type(header_bytes: bytes) -> str:
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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_bucket() -> str:
    """Return the configured bucket name for the active backend."""
    return settings.MINIO_BUCKET if settings.STORAGE_BACKEND == "local" else settings.AWS_S3_BUCKET


def _get_internal_endpoint() -> str | None:
    """Return the internal S3 endpoint URL (used by the app container)."""
    return settings.MINIO_ENDPOINT_URL if settings.STORAGE_BACKEND == "local" else None


def _get_presign_endpoint() -> str | None:
    """Return the public endpoint URL for presigned URLs (used by clients).

    MinIO: MINIO_PUBLIC_ENDPOINT_URL so browsers reach localhost:9000, not minio:9000.
    AWS S3: None — boto3 uses the global endpoint automatically.
    """
    return settings.MINIO_PUBLIC_ENDPOINT_URL if settings.STORAGE_BACKEND == "local" else None


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class StorageService:
    """Handles presigned URL generation and post-upload validation."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_object_url(self, object_key: str) -> str:
        """Construct the public URL for a stored object."""
        if settings.STORAGE_BACKEND == "local":
            endpoint = settings.MINIO_PUBLIC_ENDPOINT_URL.rstrip("/")
            return f"{endpoint}/{settings.MINIO_BUCKET}/{object_key}"

        return (
            f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{object_key}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_presigned_put(
        self,
        content_type: str,
        folder: str = "avatars",
    ) -> PresignedUrlResponse:
        """Return a presigned PUT URL for direct client-to-S3 upload.

        Args:
            content_type: Client-supplied MIME type (validated against allow-list
                          before any S3 call — early rejection).
            folder: S3 key prefix (default ``avatars``).

        Returns:
            PresignedUrlResponse with upload_url, object_key, expires_in.

        Raises:
            UnsupportedFileType: If content_type is not in the allow-list.
        """
        if content_type not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileType()

        ext = ALLOWED_EXTENSIONS[content_type]
        object_key = f"{folder}/{uuid.uuid4()}.{ext}"

        session = get_s3_session()
        async with session.client(
            "s3",
            endpoint_url=_get_presign_endpoint(),
            config=get_boto_config(),
        ) as s3:
            upload_url: str = await s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": _get_bucket(),
                    "Key": object_key,
                    "ContentType": content_type,
                },
                ExpiresIn=settings.AVATAR_PRESIGNED_EXPIRES,
            )

        return PresignedUrlResponse(
            upload_url=upload_url,
            object_key=object_key,
            expires_in=settings.AVATAR_PRESIGNED_EXPIRES,
        )

    async def validate_and_get_avatar_url(self, object_key: str) -> str:
        """Validate an uploaded file by magic bytes and return its public URL.

        Downloads only the first ``_MIN_HEADER_BYTES`` from S3 — no need to
        read the whole file.  Deletes the object if validation fails to avoid
        storing garbage in the bucket.

        Args:
            object_key: The S3 key returned by generate_presigned_put().

        Returns:
            Public S3 or MinIO URL for the confirmed object.

        Raises:
            StorageObjectNotFound: Object does not exist in S3 yet.
            UnsupportedFileType: Magic bytes don't match an allowed image format.
        """
        bucket = _get_bucket()
        session = get_s3_session()
        async with session.client(
            "s3",
            endpoint_url=_get_internal_endpoint(),
            config=get_boto_config(),
        ) as s3:
            # Fetch only the header bytes — avoids reading large files
            try:
                response = await s3.get_object(
                    Bucket=bucket,
                    Key=object_key,
                    Range=f"bytes=0-{_MIN_HEADER_BYTES - 1}",
                )
                header_bytes: bytes = await response["Body"].read()
            except ClientError as exc:
                code = exc.response["Error"]["Code"]
                if code in ("NoSuchKey", "404"):
                    raise StorageObjectNotFound(object_key) from exc
                raise

            # Validate magic bytes — delete and raise on failure
            try:
                _detect_content_type(header_bytes)
            except UnsupportedFileType:
                await s3.delete_object(Bucket=bucket, Key=object_key)
                raise

        return self._build_object_url(object_key)

    async def delete_object(self, object_key: str) -> None:
        """Delete an object from S3 (e.g. when a user removes their avatar)."""
        session = get_s3_session()
        async with session.client(
            "s3",
            endpoint_url=_get_internal_endpoint(),
            config=get_boto_config(),
        ) as s3:
            await s3.delete_object(Bucket=_get_bucket(), Key=object_key)
