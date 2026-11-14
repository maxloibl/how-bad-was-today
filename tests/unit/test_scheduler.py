"""Unit tests for the scheduler's target-date computation.

These are pure and never touch the database: ``next_target_date`` maps any
timezone-aware instant to the previous Europe/Berlin calendar day.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from daily_signal.jobs.scheduler import next_target_date

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
