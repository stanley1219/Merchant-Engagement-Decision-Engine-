from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)

    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://vera:vera_dev_password@localhost:5432/vera")
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    DATABASE_POOL_TIMEOUT: int = Field(default=30)

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS: int = Field(default=20)
    REDIS_SOCKET_TIMEOUT: int = Field(default=5)
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5)

    # Gemini API
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash-exp")
    GEMINI_TEMPERATURE: float = Field(default=0.0)
    GEMINI_MAX_TOKENS: int = Field(default=1024)

    # Security
    API_KEY_HEADER: str = Field(default="X-API-Key")
    ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])

    # Observability
    OTEL_SERVICE_NAME: str = Field(default="vera-message-engine")
    OTEL_EXPORTER_PROMETHEUS_PORT: int = Field(default=9464)
    SENTRY_DSN: str = Field(default="")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)

    # Suppression
    DEFAULT_SUPPRESSION_TTL: int = Field(default=86400)
    MAX_SUPPRESSION_TTL: int = Field(default=604800)

    # Tick Processing
    TICK_BATCH_SIZE: int = Field(default=20)
    TICK_TIMEOUT: int = Field(default=25)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()