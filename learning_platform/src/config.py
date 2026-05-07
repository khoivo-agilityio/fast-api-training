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

    # Redis — required, must be set in .env
    REDIS_URL: str

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
