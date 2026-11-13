"""SQLAlchemy implementation of :class:`DailyReportRepository`.

Publication is the single gate: every query filters ``status='published'`` and
``is_current=true``, so superseded, draft, validated and withdrawn revisions
(and their stories) are never returned. Stories are loaded ordered by rank and
their sources are loaded in one grouped query. Attribution comes from the
``story_sources`` snapshot; timestamps and language come from ``source_items``.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from daily_signal.application.ports.repositories import (
    DailyReportRecord,
    ReportRecord,
    StoryRecord,
    StorySourceRecord,
)
from daily_signal.domain.enums import (
    Category,
    Confidence,
    ContentBasis,
    DayLabel,
    Direction,
    Region,
)
from daily_signal.infrastructure.db import models


def _require[T](value: T | None, field: str) -> T:
    """Return ``value``, raising if a published row has a NULL required field."""
    if value is None:
        raise RuntimeError(f"published report has NULL {field}")
    return value


def _report_record(report: models.DailyReport, story_count: int) -> ReportRecord:
    """Map a report row to a :class:`ReportRecord` (published rows only)."""
    return ReportRecord(
        id=report.id,
        report_date=report.report_date,
        revision=report.revision,
        headline=_require(report.headline, "headline"),
        summary=_require(report.summary, "summary"),
        score=_require(report.score, "score"),
        raw_score=_require(report.raw_score, "raw_score"),
        score_label=DayLabel(_require(report.score_label, "score_label")),
        score_confidence=Confidence(_require(report.score_confidence, "score_confidence")),
        score_explanation=_require(report.score_explanation, "score_explanation"),
        methodology_version=report.methodology_version,
        published_at=_require(report.published_at, "published_at"),
        story_count=story_count,
    )


def _source_record(source: models.StorySource, item: models.SourceItem) -> StorySourceRecord:
    """Map a story-source snapshot joined with its item to a record."""
    return StorySourceRecord(
        id=item.id,
        source_id=item.source_id,
        publisher=source.publisher_snapshot,
        url=source.url_snapshot,
        original_title=source.title_snapshot,
        author=source.author_snapshot,
        published_at=item.published_at,
        updated_at=item.updated_at,
        language=item.language,
        license_code=source.license_code_snapshot,
        license_url=source.license_url_snapshot,
        attribution=source.attribution_snapshot,
        originating_agency=source.origin_agency_snapshot,
        content_modified=source.content_modified,
        modification_notice=source.modification_notice,
    )


def _story_record(
    story: models.DailyReportStory, sources: tuple[StorySourceRecord, ...]
) -> StoryRecord:
    """Map a story row and its pre-grouped sources to a record."""
    return StoryRecord(
        id=story.id,
        rank=story.rank,
        title=story.title,
        summary=story.summary,
        why_it_matters=story.why_it_matters,
        category=Category(story.category),
        region=Region(story.region),
        direction=Direction(story.direction),
        impact=story.impact,
        content_basis=ContentBasis(story.content_basis),
        derivative_license_code=story.derivative_license_code,
        derivative_license_url=story.derivative_license_url,
        modification_notice=story.modification_notice,
        sources=sources,
    )


class SqlAlchemyDailyReportRepository:
    """Read-only repository over the published report tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_by_date(self, report_date: date) -> DailyReportRecord | None:
        report = (
            await self._session.scalars(
                self._published_reports().where(models.DailyReport.report_date == report_date)
            )
        ).first()
        if report is None:
            return None
        stories = await self._load_stories(report.id)
        return DailyReportRecord(**asdict(_report_record(report, len(stories))), stories=stories)

    async def get_latest(self) -> DailyReportRecord | None:
        report = (
            await self._session.scalars(
                self._published_reports()
                .order_by(
                    models.DailyReport.report_date.desc(),
                    models.DailyReport.published_at.desc(),
                )
                .limit(1)
            )
        ).first()
        if report is None:
            return None
        stories = await self._load_stories(report.id)
        return DailyReportRecord(**asdict(_report_record(report, len(stories))), stories=stories)

    async def list_current(self, from_date: date, to_date: date) -> list[ReportRecord]:
        story_count = (
            select(func.count(models.DailyReportStory.id))
            .where(models.DailyReportStory.report_id == models.DailyReport.id)
            .scalar_subquery()
        )
        rows = (
            await self._session.execute(
                select(models.DailyReport, story_count.label("story_count"))
                .where(
                    models.DailyReport.status == "published",
                    models.DailyReport.is_current.is_(True),
                    models.DailyReport.report_date >= from_date,
                    models.DailyReport.report_date <= to_date,
                )
                .order_by(models.DailyReport.report_date.asc())
            )
        ).all()
        return [_report_record(report, count) for report, count in rows]

    async def get_current_story(self, story_id: UUID) -> StoryRecord | None:
        story = (
            await self._session.scalars(
                select(models.DailyReportStory)
                .join(
                    models.DailyReport,
                    models.DailyReport.id == models.DailyReportStory.report_id,
                )
                .where(
                    models.DailyReportStory.id == story_id,
                    models.DailyReport.status == "published",
                    models.DailyReport.is_current.is_(True),
                )
            )
        ).first()
        if story is None:
            return None
        sources = await self._load_sources([story.id])
        return _story_record(story, sources.get(story.id, ()))

    def _published_reports(self) -> Select[models.DailyReport]:
        """Base query restricted to current published report revisions."""
        return select(models.DailyReport).where(
            models.DailyReport.status == "published",
            models.DailyReport.is_current.is_(True),
        )

    async def _load_stories(self, report_id: UUID) -> tuple[StoryRecord, ...]:
        stories = (
            await self._session.scalars(
                select(models.DailyReportStory)
                .where(models.DailyReportStory.report_id == report_id)
                .order_by(models.DailyReportStory.rank.asc())
            )
        ).all()
        sources = await self._load_sources([story.id for story in stories])
        return tuple(_story_record(story, sources.get(story.id, ())) for story in stories)

    async def _load_sources(
        self, story_ids: list[UUID]
    ) -> dict[UUID, tuple[StorySourceRecord, ...]]:
        """Load and group every source snapshot for ``story_ids`` in one query."""
        if not story_ids:
            return {}
        rows = (
            await self._session.execute(
                select(models.StorySource, models.SourceItem)
                .join(models.SourceItem, models.SourceItem.id == models.StorySource.item_id)
                .where(models.StorySource.story_id.in_(story_ids))
                .order_by(
                    models.StorySource.story_id.asc(),
                    models.SourceItem.published_at.asc(),
                    models.SourceItem.id.asc(),
                )
            )
        ).all()
        grouped: dict[UUID, list[StorySourceRecord]] = {}
        for source, item in rows:
            grouped.setdefault(source.story_id, []).append(_source_record(source, item))
        return {story_id: tuple(records) for story_id, records in grouped.items()}
