"""Unit tests for advisory-lock release failure handling."""

import logging

import pytest

from daily_signal.infrastructure.db.locks import release_advisory_lock


class _ExplodingSession:
    """A session whose unlock statement fails and records invalidation."""

    def __init__(self) -> None:
        self.invalidated = False

    async def execute(self, *args: object, **kwargs: object) -> object:
        raise RuntimeError("connection reset by peer")

    async def invalidate(self) -> None:
        self.invalidated = True


async def test_release_invalidates_connection_on_unlock_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    session = _ExplodingSession()
    with caplog.at_level(logging.WARNING, logger="daily_signal.infrastructure.db.locks"):
        released = await release_advisory_lock(session, 728191)

    assert released is False
    assert session.invalidated is True
    assert any(record.getMessage() == "advisory_lock_release_failed" for record in caplog.records)
