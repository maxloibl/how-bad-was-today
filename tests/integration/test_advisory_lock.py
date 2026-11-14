"""Integration tests for the PostgreSQL session-level advisory lock."""

import logging

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from daily_signal.infrastructure.db.locks import release_advisory_lock, try_advisory_lock
from daily_signal.jobs.scheduler import DAILY_ANALYSIS_LOCK_KEY

pytestmark = pytest.mark.integration


async def test_advisory_lock_is_exclusive(
    session_factory: async_sessionmaker,
    clean_tables,
    migrated_database: str,
) -> None:
    async with session_factory() as first, session_factory() as second:
        assert await try_advisory_lock(first, DAILY_ANALYSIS_LOCK_KEY) is True
        assert await try_advisory_lock(second, DAILY_ANALYSIS_LOCK_KEY) is False
        await release_advisory_lock(first, DAILY_ANALYSIS_LOCK_KEY)
        assert await try_advisory_lock(second, DAILY_ANALYSIS_LOCK_KEY) is True
        await release_advisory_lock(second, DAILY_ANALYSIS_LOCK_KEY)


async def test_release_without_lock_invalidates_and_warns(
    session_factory: async_sessionmaker,
    clean_tables,
    migrated_database: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    async with session_factory() as session:
        with caplog.at_level(logging.WARNING, logger="daily_signal.infrastructure.db.locks"):
            released = await release_advisory_lock(session, DAILY_ANALYSIS_LOCK_KEY)

    assert released is False
    assert any(record.getMessage() == "advisory_lock_not_held" for record in caplog.records)
