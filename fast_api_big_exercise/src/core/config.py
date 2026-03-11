"""Application settings management.

All settings are loaded from .env file with fallback defaults.
Pydantic Settings automatically reads from environment variables.
"""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings - ALL loaded from .env file.

    Pydantic Settings automatically:
    1. Reads from .env file (if it exists)
    2. Reads from environment variables
    3. Uses default values as fallback

    Priority: Environment Variables > .env file > Defaults
    """

    model_config = SettingsConfigDict(
        env_file=".env",  # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=True,  # Variable names are case-sensitive
        extra="ignore",  # Ignore extra variables in .env
        str_strip_whitespace=True,  # Auto-strip whitespace
        validate_assignment=True,  # Validate when setting attributes
    )

    # ========================================================================
    # ENVIRONMENT
    # ========================================================================
    ENV: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Application environment (affects logging, debug mode, etc.)",
    )

    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging, auto-reload, etc.)",
    )

    # ========================================================================
    # APPLICATION
    # ========================================================================
    APP_NAME: str = Field(
        default="Task Manager API",
        min_length=1,
        max_length=100,
        description="Application name (shown in API docs)",
    )

    APP_VERSION: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",
        description="Application version (semantic versioning)",
    )

    API_PREFIX: str = Field(
        default="/api/v1",
        description="API route prefix",
    )

    # ========================================================================
    # SERVER
    # ========================================================================
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host (0.0.0.0 = all interfaces)",
    )

    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port (1-65535)",
    )

    RELOAD: bool = Field(
        default=True,
        description="Enable auto-reload on code changes (dev only)",
    )

    # ========================================================================
    # DATABASE
    # ========================================================================
    DATABASE_URL: str = Field(
        default="sqlite:///./taskmanager.db",
        min_length=1,
        description="Database connection string",
    )

    DB_ECHO: bool = Field(
        default=False,
        description="Log all SQL queries (useful for debugging)",
    )

    # ========================================================================
    # SECURITY
    # ========================================================================
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        min_length=32,
        description="Secret key for JWT (min 32 chars, CHANGE IN PRODUCTION!)",
    )

    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,
        description="Access token expiration (1-1440 minutes)",
    )

    # ========================================================================
    # CORS
    # ========================================================================
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins (comma-separated in .env)",
    )

    # ========================================================================
    # LOGGING
    # ========================================================================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    LOG_FORMAT: Literal["json", "console"] = Field(
        default="console",
        description="Log format (json for production, console for dev)",
    )

    # ========================================================================
    # PAGINATION
    # ========================================================================
    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Default items per page (1-100)",
    )

    MAX_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum items per page (1-1000)",
    )

    # ========================================================================
    # VALIDATORS
    # ========================================================================
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls: type[Self], v: str) -> str:
        """Ensure SECRET_KEY is secure in production."""
        import os

        if "your-secret-key" in v.lower() and os.getenv("ENV") == "production":
            raise ValueError(
                "🚨 Cannot use default SECRET_KEY in production! "
                "Generate with: openssl rand -hex 32"
            )
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls: type[Self], v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle comma-separated string from .env
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENV == "development"

    def __repr__(self) -> str:
        """Safe string representation (hides sensitive data)."""
        return (
            f"Settings("
            f"ENV={self.ENV}, "
            f"APP_NAME={self.APP_NAME}, "
            f"DATABASE_URL=*****, "
            f"SECRET_KEY=*****"
            f")"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton).

    All settings are automatically loaded from .env file.
    """
    return Settings()


settings = get_settings()
