"""
S3/MinIO client factory — aioboto3 session factory.

Reads credentials from the correct env var group based on STORAGE_BACKEND:
  - "local"  → MINIO_* vars (points at local MinIO container)
  - "s3"     → AWS_* vars  (points at AWS S3)

aioboto3.Session holds no network connections (unlike the client),
so it is safe and cheap to create a new one per call.
"""

import aioboto3
from botocore.config import Config

from src.config import settings


def get_s3_session() -> aioboto3.Session:
    """Create a fresh aioboto3 Session configured from settings."""
    if settings.STORAGE_BACKEND == "local":
        return aioboto3.Session(
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name=settings.MINIO_REGION,
        )
    return aioboto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def get_boto_config() -> Config:
    """Return botocore Config — path-style for MinIO, virtual-hosted for AWS S3."""
    # MinIO requires path-style; AWS S3 uses virtual-hosted (auto-detected)
    is_local = settings.STORAGE_BACKEND == "local"
    return Config(
        signature_version="s3v4",
        s3={"addressing_style": "path" if is_local else "auto"},
    )
