from daily_signal.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(database_url="postgresql+asyncpg://u:p@localhost/db")
    assert settings.rate_limit_per_minute == 120
    assert settings.scheduler_tick_seconds == 900
    assert settings.cors_origins == []


def test_built_database_url_percent_encodes_credentials() -> None:
    settings = Settings(
        postgres_user="user@name",
        postgres_password="p@ss/w:rd#$",
        postgres_host="db",
        postgres_port=5432,
        postgres_db="daily_signal",
    )

    assert settings.resolved_database_url == (
        "postgresql+asyncpg://user%40name:p%40ss%2Fw%3Ard%23%24@db:5432/daily_signal"
    )


def test_explicit_database_url_still_overrides_discrete_fields() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://explicit:override@host:6543/explicit_db",
        postgres_user="ignored",
        postgres_password="ignored",
        postgres_host="ignored",
        postgres_db="ignored",
    )

    assert settings.resolved_database_url == (
        "postgresql+asyncpg://explicit:override@host:6543/explicit_db"
    )
