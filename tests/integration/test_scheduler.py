"""Integration test pinning the scheduler's current no-write semantics.

TODO(foundation): durable catch-up is not implemented. ``tick`` only claims the
advisory lock and logs that the run is due; this test pins that no
``pipeline_runs`` or report row is created. Replace it with an assertion that a
durable target-date claim row exists once the analysis workflow lands.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from daily_signal.jobs.scheduler import tick

pytestmark = pytest.mark.integration

BERLIN = ZoneInfo("Europe/Berlin")


async def test_tick_does_not_create_pipeline_run_or_report(
    session_factory: async_sessionmaker,
    clean_tables,
    migrated_database: str,
) -> None:
    due = await tick(session_factory, datetime(2026, 11, 13, 3, 30, tzinfo=BERLIN))
    assert due is True

    async with session_factory() as session:
        runs = await session.scalar(text("SELECT count(*) FROM pipeline_runs"))
        reports = await session.scalar(text("SELECT count(*) FROM daily_reports"))

    assert runs == 0
    assert reports == 0
