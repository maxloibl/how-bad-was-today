"""Mapping from application records to public API DTOs."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Literal

from daily_signal.api.schemas.days import DailyReport, DayCollection, DayScore, DaySummary
from daily_signal.api.schemas.stories import Story, StoryCollection, StorySource
from daily_signal.application.ports.repositories import (
    DailyReportRecord,
    ReportRecord,
    StoryRecord,
    StorySourceRecord,
)

TIMEZONE: Literal["Europe/Berlin"] = "Europe/Berlin"
MAX_STORIES = 8


def day_score(record: ReportRecord) -> DayScore:
    """Build the day score DTO from a report record."""
    return DayScore(
        value=record.score,
        max=5,
        label=record.score_label,
        raw_value=float(record.raw_score),
        confidence=record.score_confidence,
        explanation=record.score_explanation,
    )


def day_summary(record: ReportRecord) -> DaySummary:
    """Build the calendar day summary DTO from a report record."""
    return DaySummary(
        date=record.report_date,
        score=day_score(record),
        headline=record.headline,
        story_count=record.story_count,
        revision=record.revision,
        published_at=record.published_at,
    )


def story_source(record: StorySourceRecord) -> StorySource:
    """Build a story-source attribution DTO from a snapshot record."""
    return StorySource(
        id=record.id,
        source_id=record.source_id,
        publisher=record.publisher,
        url=record.url,
        original_title=record.original_title,
        author=record.author,
        published_at=record.published_at,
        updated_at=record.updated_at,
        language=record.language,
        license_code=record.license_code,
        license_url=record.license_url,
        attribution=record.attribution,
        originating_agency=record.originating_agency,
        content_modified=record.content_modified,
        modification_notice=record.modification_notice,
    )


def story(record: StoryRecord) -> Story:
    """Build a story DTO from a story snapshot record."""
    return Story(
        id=record.id,
        rank=record.rank,
        title=record.title,
        summary=record.summary,
        why_it_matters=record.why_it_matters,
        category=record.category,
        region=record.region,
        direction=record.direction,
        impact=record.impact,
        content_basis=record.content_basis,
        derivative_license=record.derivative_license_code,
        derivative_license_url=record.derivative_license_url,
        modification_notice=record.modification_notice,
        sources=[story_source(source) for source in record.sources],
    )


def daily_report(record: DailyReportRecord) -> DailyReport:
    """Build the full daily report DTO from a report record with stories."""
    return DailyReport(
        date=record.report_date,
        score=day_score(record),
        headline=record.headline,
        story_count=record.story_count,
        revision=record.revision,
        published_at=record.published_at,
        timezone=TIMEZONE,
        summary=record.summary,
        methodology_version=record.methodology_version,
        stories=[story(item) for item in record.stories],
    )


def day_collection(
    from_date: date, to_date: date, records: Sequence[ReportRecord]
) -> DayCollection:
    """Build the calendar collection DTO for a requested range."""
    # ``from`` is a Python keyword, so the field is ``from_`` with an explicit
    # wire alias; validate the aliased mapping rather than calling the
    # generated ``__init__``.
    return DayCollection.model_validate(
        {
            "from": from_date,
            "to": to_date,
            "days": [day_summary(record) for record in records],
        }
    )


def story_collection(report_date: date, records: Sequence[StoryRecord]) -> StoryCollection:
    """Build the filtered story collection DTO for a report date."""
    return StoryCollection(
        date=report_date,
        stories=[story(record) for record in records[:MAX_STORIES]],
    )
