"""FastAPI dependencies: settings and database session access."""

from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from daily_signal.application.ports.repositories import DailyReportRepository, SourceRepository
from daily_signal.core.config import Settings
from daily_signal.infrastructure.db.repositories.reports import SqlAlchemyDailyReportRepository
from daily_signal.infrastructure.db.repositories.sources import SqlAlchemySourceRepository


def get_settings(request: Request) -> Settings:
    """Return the application settings bound to ``app.state``."""
    return cast(Settings, request.app.state.settings)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yield a database session bound to the application's session factory."""
    session_factory = cast(async_sessionmaker[AsyncSession], request.app.state.session_factory)
    async with session_factory() as session:
        yield session


async def get_report_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DailyReportRepository:
    """Build the read-only daily-report repository for the request."""
    return SqlAlchemyDailyReportRepository(session)


async def get_source_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SourceRepository:
    """Build the read-only approved-source repository for the request."""
    return SqlAlchemySourceRepository(session)
