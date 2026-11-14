"""PostgreSQL session-level advisory locks.

Advisory locks are cooperative and application-defined: they let independent
worker/scheduler processes agree that only one of them performs a given unit of
work at a time. Daily Signal uses a *session*-level lock so the lock is held
across the whole critical section and released explicitly (or when the
connection closes), rather than being tied to a single transaction.

The functions here never swallow errors: a caller that fails to acquire the
lock must be able to distinguish that from a database failure. ``pg_try_
advisory_lock`` returns ``False`` (never blocks) when another session holds the
lock, and ``pg_advisory_unlock`` returns ``False`` when this session did not
hold it.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


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


async def release_advisory_lock(session: AsyncSession, key: int) -> None:
    """Release the session-level advisory lock ``key`` if this session holds it.

    A no-op when the session does not hold the lock, which keeps release safe to
    call from ``finally`` blocks on every path.
    """
    await session.execute(
        text("SELECT pg_advisory_unlock(:key)"),
        {"key": key},
    )
