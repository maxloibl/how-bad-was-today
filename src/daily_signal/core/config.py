"""Application settings loaded from the environment and ``.env`` files."""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Daily Signal service.

    Values are read from environment variables (case-insensitive) and a
    local ``.env`` file, with the defaults below when they are absent.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    #: Optional explicit override. When unset, the URL is built from the
    #: discrete ``postgres_*`` fields with percent-encoded credentials.
    database_url: str | None = None
    postgres_user: str = "daily_signal"
    postgres_password: str = "daily_signal"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "daily_signal"
    app_env: str = "local"
    log_level: str = "INFO"
    rate_limit_per_minute: int = 120
    scheduler_tick_seconds: int = 900
    cors_origins: list[str] = []
    sources_config_path: Path = Path("config/sources.yaml")
    methodology_config_path: Path = Path("config/methodology.yaml")

    @property
    def resolved_database_url(self) -> str:
        """Return the SQLAlchemy asyncpg URL for the configured database."""
        if self.database_url:
            return self.database_url
        user = quote(self.postgres_user, safe="")
        password = quote(self.postgres_password, safe="")
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
