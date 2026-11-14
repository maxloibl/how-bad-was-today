"""Unit tests for the scheduler's target-date computation and tick logic.

The tick tests use a fake session factory so they exercise the control flow
(due gate, lock acquisition/release, no writes) without a database. The
"no pipeline_runs row" guarantee is also pinned against the real database in
``tests/integration/test_scheduler.py``.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Self
from zoneinfo import ZoneInfo

import pytest

from daily_signal.jobs import scheduler
from daily_signal.jobs.scheduler import next_target_date, tick

BERLIN = ZoneInfo("Europe/Berlin")


def test_target_date_is_the_previous_berlin_day() -> None:
    assert (
        next_target_date(datetime(2026, 11, 13, 3, 30, tzinfo=BERLIN)).isoformat() == "2026-11-12"
    )


def test_target_date_rolls_over_at_midnight() -> None:
    assert next_target_date(datetime(2026, 1, 1, 0, 5, tzinfo=BERLIN)).isoformat() == "2025-12-31"


def test_target_date_converts_utc_instants_to_berlin() -> None:
    # 2026-11-12 23:30 UTC is already 2026-11-13 00:30 in Berlin (CET), so the
    # previous Berlin day is 2026-11-12, not 2026-11-11.
    assert next_target_date(datetime(2026, 11, 12, 23, 30, tzinfo=UTC)).isoformat() == "2026-11-12"


class _FakeResult:
    def __init__(self, value: bool) -> None:
        self._value = value

    def scalar_one(self) -> bool:
        return self._value


class _FakeSession:
    """Records the SQL it is asked to run; optionally refuses the lock."""

    def __init__(self, acquire: bool = True) -> None:
        self._acquire = acquire
        self.statements: list[str] = []
        self.invalidated = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def execute(self, statement: Any, params: Any = None) -> _FakeResult:
        sql = str(statement)
        self.statements.append(sql)
        if "pg_try_advisory_lock" in sql:
            return _FakeResult(self._acquire)
        return _FakeResult(True)

    async def invalidate(self) -> None:
        self.invalidated = True


class _FakeFactory:
    def __init__(self, session: _FakeSession) -> None:
        self._session = session
        self.opened = 0

    def __call__(self) -> _FakeSession:
        self.opened += 1
        return self._session


async def test_tick_before_start_is_not_due_and_opens_no_session() -> None:
    factory = _FakeFactory(_FakeSession())
    assert await tick(factory, datetime(2026, 11, 13, 3, 29, tzinfo=BERLIN)) is False
    assert factory.opened == 0


async def test_tick_after_start_acquires_logs_and_releases(
    caplog: pytest.LogCaptureFixture,
) -> None:
    session = _FakeSession(acquire=True)
    factory = _FakeFactory(session)
    with caplog.at_level(logging.INFO, logger="daily_signal.jobs.scheduler"):
        assert await tick(factory, datetime(2026, 11, 13, 3, 30, tzinfo=BERLIN)) is True

    assert factory.opened == 1
    assert any("pg_try_advisory_lock" in statement for statement in session.statements)
    assert any("pg_advisory_unlock" in statement for statement in session.statements)
    # Only the two lock statements run: no pipeline_runs or report row is written.
    assert len(session.statements) == 2
    due = [record for record in caplog.records if record.getMessage() == "daily_analysis_due"]
    assert due and getattr(due[0], "target_date", None) == "2026-11-12"


async def test_tick_returns_false_and_does_not_unlock_when_lock_held_elsewhere() -> None:
    session = _FakeSession(acquire=False)
    factory = _FakeFactory(session)
    assert await tick(factory, datetime(2026, 11, 13, 4, 0, tzinfo=BERLIN)) is False
    assert not any("pg_advisory_unlock" in statement for statement in session.statements)


async def test_tick_releases_lock_when_body_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession(acquire=True)
    factory = _FakeFactory(session)

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("logging exploded")

    monkeypatch.setattr(scheduler.logger, "info", _boom)
    with pytest.raises(RuntimeError, match="logging exploded"):
        await tick(factory, datetime(2026, 11, 13, 4, 0, tzinfo=BERLIN))
    assert any("pg_advisory_unlock" in statement for statement in session.statements)
