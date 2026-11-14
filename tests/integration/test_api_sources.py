from uuid import uuid4

import pytest
from sqlalchemy import select

from daily_signal.infrastructure.db.models import NewsSource, SourcePermission
from tests.contract.validation import assert_valid

pytestmark = pytest.mark.integration


async def test_seed_sources_are_not_public(client, seeded_sources) -> None:
    response = await client.get("/v1/sources")
    assert response.status_code == 200
    assert response.json() == {"sources": []}


async def test_only_approved_enabled_sources_with_approved_permission_are_public(
    client, session_factory, seeded_sources
) -> None:
    async with session_factory() as session:
        source = await session.scalar(select(NewsSource).where(NewsSource.slug == "global-voices"))
        assert source is not None
        source.review_status = "approved"
        source.enabled = True
        permission = await session.scalar(
            select(SourcePermission).where(SourcePermission.source_id == source.id)
        )
        assert permission is not None
        permission.review_status = "approved"
        permission.approved_by = "test"
        permission.approved_at = permission.created_at
        await session.commit()

    response = await client.get("/v1/sources")
    assert response.status_code == 200
    assert_valid(response.json(), "SourceCollection")
    assert [source["slug"] for source in response.json()["sources"]] == ["global-voices"]
    assert response.json()["sources"][0]["licenseCode"] == "CC-BY-3.0"


async def test_latest_permission_revision_must_be_approved(
    client, session_factory, seeded_sources
) -> None:
    async with session_factory() as session:
        source = await session.scalar(select(NewsSource).where(NewsSource.slug == "global-voices"))
        assert source is not None
        source.review_status = "approved"
        source.enabled = True
        first = await session.scalar(
            select(SourcePermission).where(SourcePermission.source_id == source.id)
        )
        assert first is not None
        first.review_status = "approved"
        first.approved_by = "test"
        first.approved_at = first.created_at
        session.add(
            SourcePermission(
                id=uuid4(),
                source_id=source.id,
                revision=2,
                review_status="in_review",
                license_code=first.license_code,
                license_url=first.license_url,
                terms_url=first.terms_url,
                content_scope=first.content_scope,
                attribution_requirements=first.attribution_requirements,
            )
        )
        await session.commit()

    response = await client.get("/v1/sources")
    assert response.json() == {"sources": []}


async def test_approved_but_disabled_source_is_not_public(
    client, session_factory, seeded_sources
) -> None:
    async with session_factory() as session:
        source = await session.scalar(select(NewsSource).where(NewsSource.slug == "global-voices"))
        assert source is not None
        source.review_status = "approved"
        source.enabled = False
        permission = await session.scalar(
            select(SourcePermission).where(SourcePermission.source_id == source.id)
        )
        assert permission is not None
        permission.review_status = "approved"
        permission.approved_by = "test"
        permission.approved_at = permission.created_at
        await session.commit()

    response = await client.get("/v1/sources")
    assert response.json() == {"sources": []}


async def test_approved_enabled_source_without_permission_is_not_public(
    client, session_factory, seeded_sources
) -> None:
    async with session_factory() as session:
        existing = await session.scalar(
            select(NewsSource).where(NewsSource.slug == "global-voices")
        )
        assert existing is not None
        session.add(
            NewsSource(
                id=uuid4(),
                publisher_group_id=existing.publisher_group_id,
                slug="no-permission",
                name="No Permission",
                homepage_url="https://no-permission.example.test/",
                source_type="editorial",
                origin_country="DE",
                primary_language="de",
                review_status="approved",
                enabled=True,
            )
        )
        await session.commit()

    response = await client.get("/v1/sources")
    assert response.json() == {"sources": []}


async def test_methodology_returns_pinned_values(client) -> None:
    response = await client.get("/v1/methodology")
    assert response.status_code == 200
    assert_valid(response.json(), "Methodology")
    assert response.json()["timezone"] == "Europe/Berlin"
    assert response.json()["scoreScale"] == 5
    assert response.json()["relevanceWeights"] == {"impact": 100}
    assert response.json()["scoreThresholds"] == [-1.1, -0.3, 0.3, 1.1]
    assert response.json()["scoreColors"] == {
        "very_negative": "#CF6666",
        "negative": "#DE9A57",
        "mixed": "#B8AC69",
        "positive": "#85B78A",
        "very_positive": "#43A779",
    }
