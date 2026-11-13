"""Read ports for the public report and story surface.

Every record here is an immutable snapshot of published data: the
implementation guarantees that superseded, draft, validated and withdrawn
reports never leak through these methods.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from daily_signal.domain.enums import (
    Category,
    Confidence,
    ContentBasis,
    DayLabel,
    Direction,
    Region,
    SourceType,
)


@dataclass(frozen=True)
class ReportRecord:
    """A single published report revision, without its stories."""

    id: UUID
    report_date: date
    revision: int
    headline: str
    summary: str
    score: int
    raw_score: Decimal
    score_label: DayLabel
    score_confidence: Confidence
    score_explanation: str
    methodology_version: str
    published_at: datetime
    story_count: int


@dataclass(frozen=True)
class StorySourceRecord:
    """The attribution snapshot for one source item backing a story."""

    id: UUID
    source_id: UUID
    publisher: str
    url: str
    original_title: str | None
    author: str | None
    published_at: datetime
    updated_at: datetime | None
    language: str
    license_code: str | None
    license_url: str | None
    attribution: str | None
    originating_agency: str | None
    content_modified: bool
    modification_notice: str | None


@dataclass(frozen=True)
class StoryRecord:
    """One ranked story snapshot with its sources."""

    id: UUID
    rank: int
    title: str
    summary: str
    why_it_matters: str
    category: Category
    region: Region
    direction: Direction
    impact: int
    content_basis: ContentBasis
    derivative_license_code: str | None
    derivative_license_url: str | None
    modification_notice: str | None
    sources: tuple[StorySourceRecord, ...]


@dataclass(frozen=True)
class DailyReportRecord(ReportRecord):
    """A published report revision together with its ranked stories."""

    stories: tuple[StoryRecord, ...]


@dataclass(frozen=True)
class SourceRecord:
    """A publicly approved news source with its current permission licence."""

    id: UUID
    slug: str
    name: str
    website: str
    role: SourceType
    origin_country: str
    primary_language: str
    license_code: str | None


class DailyReportRepository(Protocol):
    """Read-only access to published reports and their story snapshots."""

    async def get_current_by_date(self, report_date: date) -> DailyReportRecord | None: ...

    async def get_latest(self) -> DailyReportRecord | None: ...

    async def list_current(self, from_date: date, to_date: date) -> list[ReportRecord]: ...

    async def get_current_story(self, story_id: UUID) -> StoryRecord | None: ...


class SourceRepository(Protocol):
    """Read-only access to sources approved for public attribution."""

    async def list_approved(self) -> list[SourceRecord]: ...
