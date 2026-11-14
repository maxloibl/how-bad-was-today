"""PostgreSQL session-level advisory locks.

Advisory locks are cooperative and application-defined: they let independent
worker/scheduler processes agree that only one of them performs a given unit of
work at a time. Daily Signal uses a *session*-level lock so the lock is held
across the whole critical section and released explicitly (or when the
connection closes), rather than being tied to a single transaction.

The functions here never swallow acquisition errors: a caller that fails to
acquire the lock must be able to distinguish that from a database failure.
``pg_try_advisory_lock`` returns ``False`` (never blocks) when another session
holds the lock. Release is best-effort but safe: if PostgreSQL reports that this
session did not hold the lock, or the unlock statement itself fails, the
connection is invalidated so it cannot be returned to the pool still holding
the lock.
"""

from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def try_advisory_lock(session: AsyncSession, key: int) -> bool:
    """Try to take the session-level advisory lock ``key`` without blocking.

    Returns ``True`` when this session acquired the lock and ``False`` when
    another session already holds it. The lock stays held until
    :func:`release_advisory_lock` is called or the session's connection closes.
    """
    result = await session.execute(
        text("SELECT pg_try_advisory_lock(:key)"),
        {"key": key},
    )
    return bool(result.scalar_one())


async def release_advisory_lock(session: AsyncSession, key: int) -> bool:
    """Release the session-level advisory lock ``key``.

    Returns ``True`` when this session held and released the lock. When
    PostgreSQL reports that the session did not hold the lock, or the unlock
    statement fails, the underlying connection is invalidated so a pooled
    connection cannot retain the lock; a warning with safe metadata only (the
    lock key and exception class, never connection details) is logged.
    """
    try:
        result = await session.execute(
            text("SELECT pg_advisory_unlock(:key)"),
            {"key": key},
        )
        released = bool(result.scalar_one())
    except Exception as exc:  # noqa: BLE001  (best-effort release must never raise)
        logger.warning(
            "advisory_lock_release_failed",
            extra={"lock_key": key, "error_type": type(exc).__name__},
        )
        await _invalidate(session, key)
        return False

    if not released:
        logger.warning("advisory_lock_not_held", extra={"lock_key": key})
        await _invalidate(session, key)
    return released


async def _invalidate(session: AsyncSession, key: int) -> None:
    """Discard the session's connection so a leaked lock cannot be pooled."""
    try:
        await session.invalidate()
    except Exception as exc:  # noqa: BLE001  (best-effort cleanup must never raise)
        logger.warning(
            "advisory_lock_invalidate_failed",
            extra={"lock_key": key, "error_type": type(exc).__name__},
        )
