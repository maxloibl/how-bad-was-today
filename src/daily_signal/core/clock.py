"""Timezone-aware clock helpers.

All report days are Europe/Berlin calendar dates, while database timestamps
are UTC. The daily analysis scheduler may start at or after 03:30 Berlin time.
"""

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")

_DAILY_ANALYSIS_START = time(3, 30)


def utc_now() -> datetime:
    """Return the current UTC-aware datetime."""
    return datetime.now(tz=UTC)


def berlin_now() -> datetime:
    """Return the current datetime in the Europe/Berlin timezone."""
    return utc_now().astimezone(BERLIN)


def berlin_today() -> date:
    """Return today's calendar date in Europe/Berlin."""
    return berlin_now().date()


def daily_analysis_due(now: datetime) -> bool:
    """Return ``True`` when the supplied instant is at/after 03:30 Berlin time.

    The instant must be timezone-aware; it is converted to Europe/Berlin before
    the threshold comparison so the answer is correct across DST transitions.
    """
    if now.tzinfo is None:
        raise ValueError("daily_analysis_due requires a timezone-aware datetime")
    berlin_time = now.astimezone(BERLIN).time()
    return berlin_time >= _DAILY_ANALYSIS_START
