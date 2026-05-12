"""
Application Configuration — pydantic-settings.

All configuration is loaded from environment variables (or .env file).
Never hardcode secrets.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database — required, must be set in .env
    DATABASE_URL: str

    # Redis — optional, set via REDIS_URL env var or Railway Redis add-on
    REDIS_URL: str | None = None

    # JWT — secret required, algorithm/expiry have safe defaults
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Quiz grading
    QUIZ_PASS_THRESHOLD: int = 70  # percent

    # App
    APP_NAME: str = "AI-Enhanced Learning Platform"
    DEBUG: bool = False

    # ---------------------------------------------------------------------------
    # S3 / MinIO — object storage for media files
    # ---------------------------------------------------------------------------
    AWS_ACCESS_KEY_ID: str = "minioadmin"
    AWS_SECRET_ACCESS_KEY: str = "minioadmin"
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "learning-platform"

    # Internal endpoint used by the app container to reach S3/MinIO.
    # Docker Compose: http://minio:9000 — leave empty for AWS S3.
    S3_ENDPOINT_URL: str | None = None

    # Public endpoint embedded in presigned PUT URLs returned to clients.
    # Browsers can't reach http://minio:9000, so set this to http://localhost:9000
    # for local dev.  Leave empty for AWS S3 (uses the global endpoint).
    S3_PUBLIC_ENDPOINT_URL: str | None = None

    # Max avatar upload size enforced in the presigned URL policy (bytes).
    AVATAR_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB

    # Presigned PUT URL validity window (seconds).
    AVATAR_PRESIGNED_EXPIRES: int = 300  # 5 minutes

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

