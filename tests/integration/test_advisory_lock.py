"""Integration tests for the PostgreSQL session-level advisory lock."""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from daily_signal.infrastructure.db.locks import release_advisory_lock, try_advisory_lock

pytestmark = pytest.mark.integration


async def test_advisory_lock_is_exclusive(
    session_factory: async_sessionmaker,
    clean_tables,
    migrated_database: str,
) -> None:
    async with session_factory() as first, session_factory() as second:
        assert await try_advisory_lock(first, 728191) is True
        assert await try_advisory_lock(second, 728191) is False
        await release_advisory_lock(first, 728191)
        assert await try_advisory_lock(second, 728191) is True
        await release_advisory_lock(second, 728191)
