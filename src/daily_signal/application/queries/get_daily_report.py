"""Queries that fetch a single published daily report or story.

Date-range validation is deliberately absent here: that is API input
validation and lives in the route layer. These functions only orchestrate the
repository and return records (or ``None`` when nothing is published).
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from daily_signal.application.ports.repositories import (
    DailyReportRecord,
    DailyReportRepository,
    StoryRecord,
)


async def get_daily_report(
    repo: DailyReportRepository, report_date: date
) -> DailyReportRecord | None:
    """Return the current published report for ``report_date``, if any."""
    return await repo.get_current_by_date(report_date)


async def get_latest_daily_report(repo: DailyReportRepository) -> DailyReportRecord | None:
    """Return the most recent current published report, if any."""
    return await repo.get_latest()


async def get_story(repo: DailyReportRepository, story_id: UUID) -> StoryRecord | None:
    """Return a story from a current published report, if any."""
    return await repo.get_current_story(story_id)
