from daily_signal.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(database_url="postgresql+asyncpg://u:p@localhost/db")
    assert settings.rate_limit_per_minute == 120
    assert settings.scheduler_tick_seconds == 900
    assert settings.cors_origins == []
