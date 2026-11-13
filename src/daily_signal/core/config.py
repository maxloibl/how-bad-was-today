"""Application settings loaded from the environment and ``.env`` files."""

from functools import lru_cache
from pathlib import Path

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

    database_url: str = "postgresql+asyncpg://daily_signal:daily_signal@localhost:5432/daily_signal"
    app_env: str = "local"
    log_level: str = "INFO"
    rate_limit_per_minute: int = 120
    scheduler_tick_seconds: int = 900
    cors_origins: list[str] = []
    sources_config_path: Path = Path("config/sources.yaml")
    methodology_config_path: Path = Path("config/methodology.yaml")


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
