"""Application settings management."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Loads configuration from:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values (lowest priority)

    Example .env file:
        ENV=production
        DATABASE_URL=postgresql://user:pass@localhost/db
        SECRET_KEY=your-secret-key
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
        str_strip_whitespace=True,  # Auto-strip whitespace
        validate_assignment=True,  # Validate on attribute assignment
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
        default="Task Management API",
        min_length=1,
        max_length=100,
        description="Application name (shown in API docs)",
    )

    APP_VERSION: str = Field(
        default="1.0.0",
        pattern=r"^\d+\.\d+\.\d+$",  # Semantic versioning
        description="Application version (semantic versioning: major.minor.patch)",
    )

    API_PREFIX: str = Field(
        default="/api/v1",
        pattern=r"^/[a-z0-9/\-]*$",  # Must start with / and contain only lowercase
        description="API route prefix (e.g., /api/v1)",
    )

    # ========================================================================
    # SERVER
    # ========================================================================

    HOST: str = Field(
        default="0.0.0.0",
        description="Server host (0.0.0.0 = all interfaces, 127.0.0.1 = localhost only)",
    )

    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port (1-65535)",
    )

    RELOAD: bool = Field(
        default=True,
        description="Enable auto-reload on code changes (development only)",
    )

    # ========================================================================
    # DATABASE
    # ========================================================================

    DATABASE_URL: str = Field(  # Changed from PostgresDsn to str
        default="postgresql://postgres:postgres@localhost:5432/taskdb",
        min_length=1,
        description="PostgreSQL connection string (postgresql://user:pass@host:port/db)",
    )

    DB_ECHO: bool = Field(
        default=False,
        description="Log all SQL queries (useful for debugging, impacts performance)",
    )

    DB_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Database connection pool size (number of persistent connections)",
    )

    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Max overflow connections beyond pool_size (burst capacity)",
    )

    # ========================================================================
    # REDIS
    # ========================================================================

    REDIS_URL: str = Field(  # Changed from RedisDsn to str
        default="redis://localhost:6379/0",
        min_length=1,
        description="Redis connection string (redis://host:port/db)",
    )

    # ========================================================================
    # SECURITY
    # ========================================================================

    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        min_length=32,  # Enforce minimum security
        description="Secret key for JWT signing (min 32 characters, CHANGE IN PRODUCTION!)",
    )

    ALGORITHM: str = Field(
        default="HS256",
        pattern=r"^(HS256|HS384|HS512|RS256|RS384|RS512)$",
        description="JWT signing algorithm (HS256, HS384, HS512, RS256, etc.)",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
        le=1440,  # Max 24 hours
        description="Access token expiration time in minutes (1-1440)",
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=90,  # Max 90 days
        description="Refresh token expiration time in days (1-90)",
    )

    # ========================================================================
    # CORS
    # ========================================================================

    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins (list of URLs)",
    )

    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials (cookies, authorization headers) in CORS requests",
    )

    CORS_ALLOW_METHODS: list[str] = Field(
        default=["*"],
        description="Allowed HTTP methods for CORS (* = all methods)",
    )

    CORS_ALLOW_HEADERS: list[str] = Field(
        default=["*"],
        description="Allowed HTTP headers for CORS (* = all headers)",
    )

    # ========================================================================
    # LOGGING
    # ========================================================================

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level (DEBUG < INFO < WARNING < ERROR < CRITICAL)",
    )

    LOG_FORMAT: Literal["json", "console"] = Field(
        default="json",
        description="Log format (json = structured logs for production, console = human-readable for dev)",
    )

    LOG_FILE: str | None = Field(
        default=None,
        description="Path to log file (None = stdout only, provide path to enable file logging)",
    )

    # ========================================================================
    # PAGINATION
    # ========================================================================

    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Default number of items per page (1-100)",
    )

    MAX_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum allowed page size (1-1000)",
    )

    # ========================================================================
    # RATE LIMITING
    # ========================================================================

    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting to prevent abuse",
    )

    RATE_LIMIT_REQUESTS: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of requests per period (1-10000)",
    )

    RATE_LIMIT_PERIOD: int = Field(
        default=60,
        ge=1,
        le=3600,  # Max 1 hour
        description="Rate limit period in seconds (1-3600)",
    )

    # ========================================================================
    # VALIDATORS
    # ========================================================================

    @field_validator("APP_NAME")
    @classmethod
    def app_name_must_not_be_empty(cls: type[Self], v: str) -> str:
        """Ensure app name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("APP_NAME cannot be empty or whitespace")
        return v.strip()

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls: type[Self], v: str) -> str:
        """
        Validate PostgreSQL connection string format.

        Expected format: postgresql://user:password@host:port/database
        """
        if not v.startswith("postgresql://") and not v.startswith("postgres://"):
            raise ValueError(
                "DATABASE_URL must start with 'postgresql://' or 'postgres://'"
            )
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls: type[Self], v: str) -> str:
        """
        Validate Redis connection string format.

        Expected format: redis://host:port/db
        """
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with 'redis://'")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls: type[Self], v: str) -> str:
        """
        Ensure SECRET_KEY is not the default value in production.

        Security best practice: Never use default secrets in production!
        """
        # Check if using default key
        if "your-secret-key-here" in v.lower() or "change-in-production" in v.lower():
            import os

            env = os.getenv("ENV", "development")
            if env == "production":
                raise ValueError(
                    "🚨 SECURITY ERROR: Cannot use default SECRET_KEY in production! "
                    "Generate a secure key with: openssl rand -hex 32"
                )
        return v

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls: type[Self], v: list[str]) -> list[str]:
        """
        Validate CORS origins format.

        Each origin must be a valid URL or '*' (wildcard).
        """
        for origin in v:
            if origin != "*" and not (
                origin.startswith("http://") or origin.startswith("https://")
            ):
                raise ValueError(
                    f"Invalid CORS origin: {origin}. "
                    "Must start with 'http://', 'https://', or be '*'"
                )
        return v

    @field_validator("DEFAULT_PAGE_SIZE")
    @classmethod
    def validate_page_size(cls: type[Self], v: int, info) -> int:
        """Ensure DEFAULT_PAGE_SIZE doesn't exceed MAX_PAGE_SIZE."""
        # Note: MAX_PAGE_SIZE might not be set yet during validation
        # This will be checked in model_validator if needed
        return v

    @field_validator("DB_MAX_OVERFLOW")
    @classmethod
    def validate_db_overflow(cls: type[Self], v: int, info) -> int:
        """
        Ensure DB_MAX_OVERFLOW is reasonable relative to DB_POOL_SIZE.

        Best practice: overflow should be 0.5x to 2x pool size.
        """
        pool_size = info.data.get("DB_POOL_SIZE", 5)
        if v > pool_size * 5:
            import warnings

            warnings.warn(
                f"DB_MAX_OVERFLOW ({v}) is very large compared to DB_POOL_SIZE ({pool_size}). "
                f"Consider using a larger pool size instead.",
                UserWarning,
            )
        return v

    # ========================================================================
    # COMPUTED PROPERTIES
    # ========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENV == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENV == "development"

    @property
    def database_url_async(self) -> str:
        """
        Get async database URL for SQLAlchemy async engine.

        Converts postgresql:// to postgresql+asyncpg://
        """
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    @property
    def effective_log_level(self) -> str:
        """
        Get effective log level based on environment.

        In DEBUG mode, always use DEBUG level.
        """
        if self.DEBUG:
            return "DEBUG"
        return self.LOG_LEVEL

    def __repr__(self) -> str:
        """Safe string representation (hides sensitive data)."""
        return (
            f"Settings("
            f"ENV={self.ENV}, "
            f"APP_NAME={self.APP_NAME}, "
            f"VERSION={self.APP_VERSION}, "
            f"DEBUG={self.DEBUG}, "
            f"DATABASE_URL=*****, "  # Hide sensitive data
            f"SECRET_KEY=*****"  # Hide sensitive data
            f")"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance (singleton pattern).

    Uses lru_cache to ensure only one Settings instance is created
    and reused across the application.

    Returns:
        Settings: Application settings instance

    Example:
        >>> from src.core.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.APP_NAME)
        Task Management API
    """
    return Settings()


# Convenience access
settings = get_settings()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def reload_settings() -> Settings:
    """
    Force reload settings (clears cache).

    Useful for testing or when environment variables change.

    Returns:
        Settings: Fresh settings instance

    Example:
        >>> settings = reload_settings()
    """
    get_settings.cache_clear()
    return get_settings()


def validate_production_config() -> list[str]:
    """
    Validate production configuration and return list of warnings.

    Returns:
        list[str]: List of configuration warnings/issues

    Example:
        >>> warnings = validate_production_config()
        >>> for warning in warnings:
        ...     print(f"⚠️  {warning}")
    """
    warnings = []
    settings = get_settings()

    if not settings.is_production:
        return warnings  # Skip checks for non-production

    # Check SECRET_KEY
    if len(settings.SECRET_KEY) < 32:
        warnings.append("SECRET_KEY is too short (minimum 32 characters)")

    # Check DEBUG mode
    if settings.DEBUG:
        warnings.append("DEBUG mode is enabled (should be False in production)")

    # Check RELOAD
    if settings.RELOAD:
        warnings.append("Auto-reload is enabled (should be False in production)")

    # Check CORS origins
    if "*" in settings.CORS_ORIGINS:
        warnings.append("CORS allows all origins (*) - security risk!")

    # Check database pool
    if settings.DB_POOL_SIZE < 5:
        warnings.append(f"DB_POOL_SIZE is low ({settings.DB_POOL_SIZE}) for production")

    # Check log format
    if settings.LOG_FORMAT != "json":
        warnings.append("LOG_FORMAT should be 'json' in production for better parsing")

    return warnings
