import pytest
from sqlalchemy import func, select

from daily_signal.infrastructure.db.models import (
    NewsSource,
    PublisherGroup,
    SourceFeed,
    SourcePermission,
)
from daily_signal.infrastructure.db.seed import load_sources_config, seed_sources

pytestmark = pytest.mark.integration


async def test_seed_is_idempotent_and_locks_rights(
    session_factory,
    clean_tables,
    migrated_database: str,
) -> None:
    config = load_sources_config("config/sources.yaml")
    async with session_factory() as session:
        first = await seed_sources(session, config)
        await session.commit()
        second = await seed_sources(session, config)
        await session.commit()
        assert first.created == 3
        assert second.created == 0

        assert await session.scalar(select(func.count()).select_from(NewsSource)) == 3
        assert await session.scalar(select(func.count()).select_from(PublisherGroup)) == 3
        assert await session.scalar(select(func.count()).select_from(SourceFeed)) == 3
        assert await session.scalar(select(func.count()).select_from(SourcePermission)) == 3

        sources = (await session.scalars(select(NewsSource))).all()
        assert all(source.review_status == "in_review" for source in sources)
        assert all(source.enabled is False for source in sources)
        permissions = (await session.scalars(select(SourcePermission))).all()
        assert all(permission.review_status == "in_review" for permission in permissions)
        assert all(permission.publish_derivatives is False for permission in permissions)
        assert all(permission.send_to_external_llm is False for permission in permissions)


async def test_seed_never_re_enables_or_downgrades_an_existing_source(
    session_factory,
    clean_tables,
    migrated_database: str,
) -> None:
    config = load_sources_config("config/sources.yaml")
    async with session_factory() as session:
        await seed_sources(session, config)
        await session.commit()
        source = await session.scalar(select(NewsSource).where(NewsSource.slug == "global-voices"))
        assert source is not None
        source.review_status = "approved"
        source.enabled = True
        await session.commit()

        await seed_sources(session, config)
        await session.commit()
        await session.refresh(source)
        assert source.review_status == "approved"
        assert source.enabled is True
