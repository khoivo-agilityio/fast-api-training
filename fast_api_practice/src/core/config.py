from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = model_config.get(
        "DATABASE_URL",
        "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice",
    )
    DATABASE_URL_TEST: str = model_config.get(
        "DATABASE_URL_TEST",
        "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_test",
    )

    # JWT
    JWT_SECRET_KEY: str = model_config.get("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = model_config.get("JWT_ALGORITHM, ", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = model_config.get(
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 15
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = model_config.get(
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS", 5
    )

    # App
    APP_NAME: str = model_config.get("APP_NAME", "Collaborative Task Manager")
    DEBUG: bool = model_config.get("DEBUG", True)

    # Email / SMTP
    # Set SMTP_ENABLED=true and fill in the credentials to send real emails.
    # When false (default) the functions only log — useful for dev/test.
    SMTP_ENABLED: bool = model_config.get("SMTP_ENABLED", False)
    SMTP_HOST: str = model_config.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = model_config.get("SMTP_PORT", 465)  # 465 = SSL, 587 = STARTTLS
    SMTP_USERNAME: str = model_config.get("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = model_config.get("SMTP_PASSWORD", "")  # App-password
    SMTP_FROM: str = model_config.get("SMTP_FROM", "")


def get_settings() -> Settings:
    return Settings()
