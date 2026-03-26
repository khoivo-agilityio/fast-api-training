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


def get_settings() -> Settings:
    return Settings()
