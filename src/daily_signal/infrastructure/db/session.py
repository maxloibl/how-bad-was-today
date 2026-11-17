"""Async engine and session factory construction."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from daily_signal.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Build an async SQLAlchemy engine for the configured database URL."""
    return create_async_engine(
        settings.resolved_database_url,
        pool_pre_ping=True,
        connect_args={"timeout": 5},
    )


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Build an async sessionmaker bound to the supplied engine."""
    return async_sessionmaker(engine, expire_on_commit=False)
