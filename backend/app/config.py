"""Centralised app configuration (Sprint 0.5).

Every runtime setting lives here and is loaded from environment variables
(optionally from a local .env file for development).  Code should import
`settings` from this module instead of calling `os.getenv()` directly so that
values are validated in one place.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    database_url: str = Field(
        default="postgresql+asyncpg://bijganit:bijganit@localhost:5432/bijganit",
        description="Async SQLAlchemy URL used by the FastAPI app.",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg2://bijganit:bijganit@localhost:5432/bijganit",
        description="Sync SQLAlchemy URL used by Alembic migrations.",
    )
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
