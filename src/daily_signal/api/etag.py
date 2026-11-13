"""ETag construction and ``If-None-Match`` evaluation.

Report ETags are ``"<report-id>:<revision>"`` so a new revision of the same day
invalidates caches. Calendar ETags hash the requested range and the published
revisions it contains.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import date
from uuid import UUID

from daily_signal.application.ports.repositories import ReportRecord


def make_report_etag(report_id: UUID, revision: int) -> str:
    """Return the strong ETag that identifies a single report revision."""
    return f'"{report_id}:{revision}"'


def make_days_etag(from_date: date, to_date: date, days: Sequence[ReportRecord]) -> str:
    """Return a strong ETag for a calendar range and its published days."""
    parts = [f"{from_date.isoformat()}..{to_date.isoformat()}"]
    parts.extend(f"{day.id}:{day.revision}" for day in days)
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f'"{digest}"'


def etag_matches(if_none_match: str | None, etag: str) -> bool:
    """Return whether an ``If-None-Match`` header selects ``etag``.

    Handles a single tag, a comma-separated list of tags, weak tags (the ``W/``
    prefix is ignored) and the ``*`` wildcard.
    """
    if not if_none_match:
        return False
    for candidate in if_none_match.split(","):
        token = candidate.strip()
        if not token:
            continue
        if token == "*":
            return True
        if token.startswith("W/"):
            token = token[2:].strip()
        if token == etag:
            return True
    return False
