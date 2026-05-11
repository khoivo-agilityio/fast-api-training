"""
Storage Service — S3/MinIO presigned URL generation and object validation.

Flow:
  1. generate_presigned_put()  →  server signs a PUT URL  →  client uploads
  2. validate_and_get_avatar_url()  →  server reads 16 header bytes from S3
                                    →  validates magic bytes
                                    →  returns CDN/MinIO URL
"""

import uuid

from botocore.exceptions import ClientError

from src.config import settings
from src.storage.client import get_boto_config, get_s3_session
from src.storage.exceptions import StorageObjectNotFound, UnsupportedFileType
from src.storage.magic import ALLOWED_EXTENSIONS, MIN_HEADER_BYTES, detect_content_type
from src.storage.schemas import PresignedUrlResponse


class StorageService:
    """Handles presigned URL generation and post-upload validation."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_object_url(self, object_key: str) -> str:
        """Construct the public URL for a stored object.

        Priority:
          1. CloudFront CDN URL  (production)
          2. S3_PUBLIC_ENDPOINT_URL / bucket / key  (local MinIO dev)
        """
        if settings.CLOUDFRONT_BASE_URL:
            base = settings.CLOUDFRONT_BASE_URL.rstrip("/")
            return f"{base}/{object_key}"

        # Local dev — MinIO public URL accessible from the browser
        endpoint = (settings.S3_PUBLIC_ENDPOINT_URL or "").rstrip("/")
        return f"{endpoint}/{settings.S3_BUCKET_NAME}/{object_key}"

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

        # Use the *public* endpoint for the presigned URL so the browser
        # can reach MinIO directly (http://localhost:9000 not http://minio:9000)
        presign_endpoint = settings.S3_PUBLIC_ENDPOINT_URL or settings.S3_ENDPOINT_URL

        session = get_s3_session()
        async with session.client(
            "s3",
            endpoint_url=presign_endpoint,
            config=get_boto_config(),
        ) as s3:
            upload_url: str = await s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.S3_BUCKET_NAME,
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

        Downloads only the first ``MIN_HEADER_BYTES`` from S3 — no need to
        read the whole file.  Deletes the object if validation fails to avoid
        storing garbage in the bucket.

        Args:
            object_key: The S3 key returned by generate_presigned_put().

        Returns:
            CDN or MinIO URL for the confirmed object.

        Raises:
            StorageObjectNotFound: Object does not exist in S3 yet.
            UnsupportedFileType: Magic bytes don't match an allowed image format.
        """
        session = get_s3_session()
        async with session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            config=get_boto_config(),
        ) as s3:
            # Fetch only the header bytes — avoids reading large files
            try:
                response = await s3.get_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=object_key,
                    Range=f"bytes=0-{MIN_HEADER_BYTES - 1}",
                )
                header_bytes: bytes = await response["Body"].read()
            except ClientError as exc:
                code = exc.response["Error"]["Code"]
                if code in ("NoSuchKey", "404"):
                    raise StorageObjectNotFound(object_key) from exc
                raise

            # Validate magic bytes — delete and raise on failure
            try:
                detect_content_type(header_bytes)
            except UnsupportedFileType:
                await s3.delete_object(
                    Bucket=settings.S3_BUCKET_NAME,
                    Key=object_key,
                )
                raise

        return self._build_object_url(object_key)

    async def delete_object(self, object_key: str) -> None:
        """Delete an object from S3 (e.g. when a user removes their avatar)."""
        session = get_s3_session()
        async with session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            config=get_boto_config(),
        ) as s3:
            await s3.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=object_key,
            )
