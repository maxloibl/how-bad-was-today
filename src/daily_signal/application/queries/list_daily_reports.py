"""Query that lists current published daily reports over a date range."""

from __future__ import annotations

from datetime import date

from daily_signal.application.ports.repositories import DailyReportRepository, ReportRecord


async def list_daily_reports(
    repo: DailyReportRepository, from_date: date, to_date: date
) -> list[ReportRecord]:
    """Return current published reports in ``[from_date, to_date]``, ascending."""
    return await repo.list_current(from_date, to_date)
