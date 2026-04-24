"""Application settings — loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration.

    All values are read from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "AI Real Estate Sales Agent"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:changeme@postgres:5432/ai_real_estate"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_STATE_TTL_SECONDS: int = 86400  # 24 hours
    REDIS_KEY_PREFIX: str = "ai_re"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Auth
    SECRET_KEY: str = "changeme-jwt-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # LLM / AI
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — call as a FastAPI dependency."""
    return Settings()
