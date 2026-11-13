"""Source DTOs matching ``contracts/openapi.yaml``."""

from __future__ import annotations

from uuid import UUID

from pydantic import ConfigDict

from daily_signal.api.schemas.base import ApiModel
from daily_signal.application.ports.repositories import SourceRecord
from daily_signal.domain.enums import SourceType


class Source(ApiModel):
    """A publicly approved news source and its current licence."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    slug: str
    name: str
    website: str
    role: SourceType
    origin_country: str
    primary_language: str
    license_code: str | None


class SourceCollection(ApiModel):
    """The list of approved sources."""

    model_config = ConfigDict(extra="forbid")

    sources: list[Source]


def source(record: SourceRecord) -> Source:
    """Build a source DTO from a repository record."""
    return Source(
        id=record.id,
        slug=record.slug,
        name=record.name,
        website=record.website,
        role=record.role,
        origin_country=record.origin_country,
        primary_language=record.primary_language,
        license_code=record.license_code,
    )


def source_collection(records: list[SourceRecord]) -> SourceCollection:
    """Build the approved-source collection DTO."""
    return SourceCollection(sources=[source(record) for record in records])
