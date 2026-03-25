from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_dev"
    DATABASE_URL_TEST: str = "postgresql+asyncpg://taskmanager:taskmanager_dev@localhost:5432/fast_api_practice_test"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production-must-be-32-plus-chars!!"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    APP_NAME: str = "Collaborative Task Manager"
    DEBUG: bool = True


def get_settings() -> Settings:
    return Settings()
