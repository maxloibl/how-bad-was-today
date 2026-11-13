"""SQLAlchemy implementation of :class:`SourceRepository`.

A source is public only when it is enabled, its own review status is
``approved``, and the *latest* permission revision is itself approved. The
latest revision is chosen with PostgreSQL ``DISTINCT ON`` so a newer
``in_review``/``suspended``/``rejected`` revision correctly hides a source
whose older revision was once approved. Sources are returned ordered by slug.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession

from daily_signal.application.ports.repositories import SourceRecord
from daily_signal.domain.enums import SourceType
from daily_signal.infrastructure.db import models


class SqlAlchemySourceRepository:
    """Read-only repository over approved, enabled news sources."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_approved(self) -> list[SourceRecord]:
        """Return every source that is currently approved for public attribution."""
        latest_permission = (
            select(
                models.SourcePermission.source_id,
                models.SourcePermission.review_status,
                models.SourcePermission.license_code,
            )
            .ext(distinct_on(models.SourcePermission.source_id))
            .order_by(
                models.SourcePermission.source_id,
                models.SourcePermission.revision.desc(),
            )
            .subquery()
        )
        rows = (
            await self._session.execute(
                select(models.NewsSource, latest_permission.c.license_code)
                .join(
                    latest_permission,
                    latest_permission.c.source_id == models.NewsSource.id,
                )
                .where(
                    models.NewsSource.enabled.is_(True),
                    models.NewsSource.review_status == "approved",
                    latest_permission.c.review_status == "approved",
                )
                .order_by(models.NewsSource.slug.asc())
            )
        ).all()
        return [
            SourceRecord(
                id=source.id,
                slug=source.slug,
                name=source.name,
                website=source.homepage_url,
                role=SourceType(source.source_type),
                origin_country=source.origin_country,
                primary_language=source.primary_language,
                license_code=license_code,
            )
            for source, license_code in rows
        ]
