from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database — must be set via .env; validator below enforces non-empty
    DATABASE_URL: str = ""
    DATABASE_URL_TEST: str = ""

    # JWT — must be set via .env; validator below enforces non-empty
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 5

    # App
    APP_NAME: str = "Collaborative Task Manager"
    DEBUG: bool = False

    # Server — Railway injects PORT; entrypoint uses ${PORT:-8000} as fallback
    PORT: int = 8000

    # Email / SMTP
    # Set SMTP_ENABLED=true and fill in the credentials to send real emails.
    # When false (default) the functions only log — useful for dev/test.
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465  # 465 = SSL, 587 = STARTTLS
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""  # App-password
    SMTP_FROM: str = ""

    @model_validator(mode="after")
    def _validate_critical_settings(self) -> "Settings":
        if not self.DATABASE_URL:
            raise ValueError(
                "DATABASE_URL must be set (e.g. in .env). Example: "
                "postgresql+asyncpg://user:pass@localhost:5432/dbname"
            )
        if not self.JWT_SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY must be set (e.g. in .env). "
                "Generate one with: "
                "python -c 'import secrets; "
                "print(secrets.token_urlsafe(64))'"
            )
        return self


def get_settings() -> Settings:
    return Settings()
