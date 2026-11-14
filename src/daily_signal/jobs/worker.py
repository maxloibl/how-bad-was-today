"""Worker heartbeat process.

The worker owns Daily Signal's asynchronous background work. In the foundation
no ingestion or analysis workflow exists yet, so the loop only probes database
connectivity and emits a heartbeat. It is deliberately defensive: every error
is logged with the exception class and message only (never article text) and
the loop continues, so a transient database outage cannot crash-loop the
process. ``stop_event`` lets the CLI shut it down cleanly on SIGTERM/SIGINT.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from daily_signal.core.config import Settings
from daily_signal.infrastructure.db.session import create_engine, create_session_factory

logger = logging.getLogger(__name__)

#: Seconds between worker heartbeats.
HEARTBEAT_SECONDS = 5.0


async def run_worker(settings: Settings, stop_event: asyncio.Event) -> None:
    """Emit a heartbeat every ``HEARTBEAT_SECONDS`` until ``stop_event`` is set.

    Each cycle probes the database with ``SELECT 1`` so connectivity problems
    surface as ``worker_error`` rather than silence. Errors never propagate:
    the loop logs and continues. The engine is always disposed on the way out.
    """
    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    logger.info("worker_started", extra={"heartbeat_seconds": HEARTBEAT_SECONDS})
    try:
        while not stop_event.is_set():
            try:
                async with session_factory() as session:
                    await session.execute(text("SELECT 1"))
                logger.info("worker_heartbeat")
            except Exception as exc:
                logger.error("worker_error", exc_info=exc)
            await _sleep_or_stop(stop_event, HEARTBEAT_SECONDS)
    finally:
        await engine.dispose()


async def _sleep_or_stop(stop_event: asyncio.Event, seconds: float) -> None:
    """Sleep ``seconds`` but return early as soon as ``stop_event`` is set."""
    try:
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)
    except TimeoutError:
        pass
