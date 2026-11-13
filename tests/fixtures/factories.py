"""Database factories shared by integration tests.

``published_report`` builds one complete, rights-cleared published day: a
publisher group, an approved+enabled source with an approved permission, a
feed, five accepted items, five events, a published current report with five
ranked stories and one attribution snapshot per story, plus a superseded
(``is_current=False``) revision whose story must stay invisible.

The five story rows mirror the task brief exactly, so the impact-squared
weighted mean is ``(-2 + 0 + 2 - 1 + 1) / (1 + 4 + 1 + 1 + 1) = 0`` and the
published day score is ``3`` / ``mixed``. That keeps the fixture's score
consistent and makes the ``direction=negative AND region=germany`` filter
return exactly one story.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from daily_signal.infrastructure.db.models import (
    DailyReport,
    DailyReportStory,
    Event,
    NewsSource,
    PublisherGroup,
    SourceFeed,
    SourceItem,
    SourcePermission,
    StorySource,
)

REPORT_DATE = date(2026, 11, 12)
PUBLISHED_AT = datetime(2026, 11, 12, 18, 30, tzinfo=UTC)
SUPERSEDED_PUBLISHED_AT = datetime(2026, 11, 12, 20, 0, tzinfo=UTC)

#: ``(rank, direction, direction_value, impact, region, category)`` per story.
_STORY_ROWS: tuple[tuple[int, str, int, int, str, str], ...] = (
    (1, "negative", -2, 1, "germany", "politics"),
    (2, "neutral", 0, 2, "europe", "economy"),
    (3, "positive", 2, 1, "world", "world"),
    (4, "negative", -1, 1, "europe", "science"),
    (5, "positive", 1, 1, "germany", "environment"),
)

_LICENSE_CODE = "CC-BY-4.0"
_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
_PUBLISHER = "Example Source"


def _published_report_fields(
    *, report_date: date, revision: int, published_at: datetime
) -> dict[str, Any]:
    """Complete, contract-valid column values for a published report row."""
    return {
        "report_date": report_date,
        "revision": revision,
        "status": "published",
        "headline": "A mixed day across Europe",
        "summary": "Five stories with offsetting directions produced a mixed day.",
        "score": 3,
        "raw_score": 0,
        "score_label": "mixed",
        "score_confidence": "high",
        "score_explanation": "Impact-weighted story directions cancel out.",
        "methodology_version": "2026.1",
        "prompt_version": "p1",
        "published_at": published_at,
    }


@pytest.fixture
async def published_report(
    session_factory: async_sessionmaker[AsyncSession],
    clean_tables: None,
) -> AsyncIterator[dict[str, Any]]:
    """Insert a rights-cleared published report and return its identifiers."""
    group_id = uuid4()
    source_id = uuid4()
    permission_id = uuid4()
    feed_id = uuid4()
    report_id = uuid4()
    superseded_report_id = uuid4()

    item_ids = [uuid4() for _ in _STORY_ROWS]
    event_ids = [uuid4() for _ in _STORY_ROWS]
    story_ids = [uuid4() for _ in _STORY_ROWS]
    superseded_story_id = uuid4()

    async with session_factory() as session:
        session.add(
            PublisherGroup(
                id=group_id,
                slug="example-group",
                name="Example Group",
                country_code="DE",
            )
        )
        await session.flush()

        session.add(
            NewsSource(
                id=source_id,
                publisher_group_id=group_id,
                slug="example-source",
                name=_PUBLISHER,
                homepage_url="https://source.example.test",
                source_type="editorial",
                origin_country="DE",
                primary_language="en",
                review_status="approved",
                enabled=True,
                reviewed_at=PUBLISHED_AT,
            )
        )
        session.add(
            SourceFeed(
                id=feed_id,
                source_id=source_id,
                feed_url="https://source.example.test/feed.xml",
                feed_kind="rss",
                enabled=True,
            )
        )
        session.add(
            SourcePermission(
                id=permission_id,
                source_id=source_id,
                revision=1,
                review_status="approved",
                license_code=_LICENSE_CODE,
                license_url=_LICENSE_URL,
                terms_url="https://source.example.test/terms",
                content_scope="metadata,analysis,derivatives",
                attribution_requirements="Attribute Example Source",
                retention_hours=72,
                fetch_metadata=True,
                fetch_full_text=True,
                analyze_content=True,
                store_temporary=True,
                store_long_term=True,
                create_adaptations=True,
                publish_derivatives=True,
                approved_by="editor@example.test",
                approved_at=PUBLISHED_AT,
            )
        )
        await session.flush()

        for index, (rank, _direction, _value, _impact, region, category) in enumerate(_STORY_ROWS):
            session.add(
                SourceItem(
                    id=item_ids[index],
                    source_id=source_id,
                    feed_id=feed_id,
                    permission_id=permission_id,
                    external_id=f"item-{rank}",
                    original_url=f"https://source.example.test/articles/{rank}",
                    canonical_url=f"https://source.example.test/articles/{rank}",
                    original_title=f"Original title {rank}",
                    author="Jane Doe",
                    language="en",
                    published_at=PUBLISHED_AT,
                    updated_at=None,
                    license_code=_LICENSE_CODE,
                    license_url=_LICENSE_URL,
                    originating_agency=None,
                    editorial_type="news",
                    ingestion_status="accepted",
                )
            )
            session.add(
                Event(
                    id=event_ids[index],
                    internal_title=f"Event {rank}",
                    event_date=REPORT_DATE,
                    region=region,
                    category=category,
                )
            )
        await session.flush()

        session.add(
            DailyReport(
                id=report_id,
                is_current=True,
                **_published_report_fields(
                    report_date=REPORT_DATE, revision=1, published_at=PUBLISHED_AT
                ),
            )
        )
        session.add(
            DailyReport(
                id=superseded_report_id,
                is_current=False,
                **_published_report_fields(
                    report_date=REPORT_DATE,
                    revision=2,
                    published_at=SUPERSEDED_PUBLISHED_AT,
                ),
            )
        )
        await session.flush()

        for index, (rank, direction, value, impact, region, category) in enumerate(_STORY_ROWS):
            session.add(
                DailyReportStory(
                    id=story_ids[index],
                    report_id=report_id,
                    event_id=event_ids[index],
                    rank=rank,
                    title=f"Story {rank} title",
                    summary=f"Story {rank} summary.",
                    why_it_matters=f"Story {rank} matters.",
                    category=category,
                    region=region,
                    direction=direction,
                    direction_value=value,
                    impact=impact,
                    content_basis="facts_synthesis",
                )
            )
        session.add(
            DailyReportStory(
                id=superseded_story_id,
                report_id=superseded_report_id,
                event_id=event_ids[0],
                rank=1,
                title="Superseded story title",
                summary="Superseded story summary.",
                why_it_matters="Superseded story matters.",
                category="politics",
                region="germany",
                direction="negative",
                direction_value=-2,
                impact=1,
                content_basis="facts_synthesis",
            )
        )
        await session.flush()

        for index, rank in enumerate(range(1, len(_STORY_ROWS) + 1)):
            session.add(
                StorySource(
                    story_id=story_ids[index],
                    item_id=item_ids[index],
                    publisher_snapshot=_PUBLISHER,
                    url_snapshot=f"https://source.example.test/articles/{rank}",
                    title_snapshot=f"Original title {rank}",
                    author_snapshot="Jane Doe",
                    license_code_snapshot=_LICENSE_CODE,
                    license_url_snapshot=_LICENSE_URL,
                    attribution_snapshot="Example Source, CC BY 4.0",
                    origin_agency_snapshot=None,
                    evidence_role="supports",
                    content_modified=False,
                    modification_notice=None,
                )
            )
        session.add(
            StorySource(
                story_id=superseded_story_id,
                item_id=item_ids[0],
                publisher_snapshot=_PUBLISHER,
                url_snapshot="https://source.example.test/articles/1",
                title_snapshot="Original title 1",
                author_snapshot="Jane Doe",
                license_code_snapshot=_LICENSE_CODE,
                license_url_snapshot=_LICENSE_URL,
                attribution_snapshot="Example Source, CC BY 4.0",
                origin_agency_snapshot=None,
                evidence_role="supports",
                content_modified=False,
                modification_notice=None,
            )
        )
        await session.commit()

    yield {
        "report_id": report_id,
        "current_story_ids": story_ids,
        "superseded_story_id": superseded_story_id,
    }
