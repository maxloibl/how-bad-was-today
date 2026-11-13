"""FastAPI dependencies: settings and database session access."""

from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from daily_signal.core.config import Settings


def get_settings(request: Request) -> Settings:
    """Return the application settings bound to ``app.state``."""
    return cast(Settings, request.app.state.settings)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a database session bound to the application's session factory."""
    session_factory = cast(async_sessionmaker[AsyncSession], request.app.state.session_factory)
    async with session_factory() as session:
        yield session
