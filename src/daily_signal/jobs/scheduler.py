"""Daily analysis scheduler.

Every ``settings.scheduler_tick_seconds`` the scheduler evaluates whether the
previous Europe/Berlin calendar day's analysis is due. Once it is due (at or
after 03:30 Berlin time) and no other process holds the PostgreSQL advisory
lock, the run is claimed and ``daily_analysis_due`` is logged.

The analysis workflow itself is not implemented in the foundation, so
:func:`tick` only claims the lock and immediately releases it: it deliberately
does not create a ``pipeline_runs`` row or a fake report. This keeps the
catch-up semantics honest (a run is retried on the next tick until the real
workflow exists) while preventing duplicate work across processes.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from daily_signal.core.clock import BERLIN, daily_analysis_due, utc_now
from daily_signal.core.config import Settings
from daily_signal.infrastructure.db.locks import release_advisory_lock, try_advisory_lock
from daily_signal.infrastructure.db.session import create_engine, create_session_factory

logger = logging.getLogger(__name__)

#: Stable PostgreSQL advisory-lock key that guards the daily analysis run.
DAILY_ANALYSIS_LOCK_KEY = 728191


def next_target_date(now: datetime) -> date:
    """Return the previous Europe/Berlin calendar day for ``now``.

    ``now`` must be timezone-aware; it is converted to Europe/Berlin first so
    the answer is correct across DST transitions and when callers pass UTC.
    """
    if now.tzinfo is None:
        raise ValueError("next_target_date requires a timezone-aware datetime")
    return now.astimezone(BERLIN).date() - timedelta(days=1)


async def tick(session_factory: async_sessionmaker[AsyncSession], now: datetime) -> bool:
    """Try to claim the daily analysis run for ``now``.

    Returns ``True`` only when the run is due *and* this process acquired the
    advisory lock; returns ``False`` before 03:30 Berlin time or when another
    process holds the lock. The lock is always released before returning, even
    if logging fails, so a later tick or another process can retry.
    """
    if not daily_analysis_due(now):
        return False

    target_date = next_target_date(now)
    async with session_factory() as session:
        if not await try_advisory_lock(session, DAILY_ANALYSIS_LOCK_KEY):
            return False
        try:
            logger.info(
                "daily_analysis_due",
                extra={"target_date": target_date.isoformat()},
            )
            return True
        finally:
            await release_advisory_lock(session, DAILY_ANALYSIS_LOCK_KEY)


async def run_scheduler(settings: Settings, stop_event: asyncio.Event) -> None:
    """Tick every ``settings.scheduler_tick_seconds`` until ``stop_event`` is set.

    Any error raised by :func:`tick` is logged (exception class and message
    only) and swallowed so a transient database outage cannot crash-loop the
    process. The engine is always disposed on the way out.
    """
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    logger.info(
        "scheduler_started",
        extra={"tick_seconds": settings.scheduler_tick_seconds},
    )
    try:
        while not stop_event.is_set():
            await _sleep_or_stop(stop_event, settings.scheduler_tick_seconds)
            if stop_event.is_set():
                break
            try:
                await tick(session_factory, utc_now())
            except Exception as exc:
                logger.error("scheduler_error", exc_info=exc)
    finally:
        await engine.dispose()


async def _sleep_or_stop(stop_event: asyncio.Event, seconds: float) -> None:
    """Sleep ``seconds`` but return early as soon as ``stop_event`` is set."""
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except TimeoutError:
        pass
