from datetime import datetime
from zoneinfo import ZoneInfo

from daily_signal.core.clock import daily_analysis_due

BERLIN = ZoneInfo("Europe/Berlin")


def test_daily_analysis_not_due_before_0330() -> None:
    assert daily_analysis_due(datetime(2026, 11, 13, 3, 29, tzinfo=BERLIN)) is False


def test_daily_analysis_due_at_and_after_0330() -> None:
    assert daily_analysis_due(datetime(2026, 11, 13, 3, 30, tzinfo=BERLIN)) is True
    assert daily_analysis_due(datetime(2026, 11, 13, 4, 0, tzinfo=BERLIN)) is True


def test_daily_analysis_uses_berlin_time_across_dst() -> None:
    # 02:30 UTC is 03:30 CET on the winter date and 04:30 CEST on the summer date.
    assert daily_analysis_due(datetime(2026, 1, 15, 2, 30, tzinfo=ZoneInfo("UTC"))) is True
    assert daily_analysis_due(datetime(2026, 7, 15, 2, 30, tzinfo=ZoneInfo("UTC"))) is True
