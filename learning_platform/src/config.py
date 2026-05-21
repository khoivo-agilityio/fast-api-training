"""
Application Configuration — pydantic-settings.

All configuration is loaded from environment variables (or .env file).
Never hardcode secrets.
"""

from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database — required, must be set in .env
    DATABASE_URL: str

    # JWT — secret required, algorithm/expiry have safe defaults
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Quiz grading
    QUIZ_PASS_THRESHOLD: int = 70  # percent

    # App
    APP_NAME: str = "AI-Enhanced Learning Platform"
    ENABLE_DEBUG: bool = False

    # CORS — comma-separated list of allowed frontend origins
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # SQLAdmin
    SQLADMIN_SECRET_KEY: str = "change-me-sqladmin-secret"

    # ---------------------------------------------------------------------------
    # Storage backend selector
    # "local"  → reads MINIO_* vars (MinIO, for local development)
    # "s3"     → reads AWS_*  vars (AWS S3, for production)
    # ---------------------------------------------------------------------------
    STORAGE_BACKEND: Literal["local", "s3"] = "local"

    # ---------------------------------------------------------------------------
    # MinIO — only read when STORAGE_BACKEND=local
    # ---------------------------------------------------------------------------
    MINIO_ENDPOINT_URL: str = "http://localhost:9000"
    MINIO_PUBLIC_ENDPOINT_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "learning-platform"
    MINIO_REGION: str = "us-east-1"

    # ---------------------------------------------------------------------------
    # AWS S3 — only read when STORAGE_BACKEND=s3
    # ---------------------------------------------------------------------------
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = ""

    # ---------------------------------------------------------------------------
    # Avatar upload limits
    # ---------------------------------------------------------------------------
    # Max avatar upload size enforced in the presigned URL policy (bytes).
    AVATAR_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB

    # Presigned PUT URL validity window (seconds).
    AVATAR_PRESIGNED_EXPIRES: int = 300  # 5 minutes

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
