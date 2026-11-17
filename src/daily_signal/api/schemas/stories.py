"""Story DTOs matching ``contracts/openapi.yaml``."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from daily_signal.api.schemas.base import ApiModel
from daily_signal.domain.enums import Category, ContentBasis, Direction, Region


class StorySource(ApiModel):
    """The attribution snapshot for one source item backing a story."""

    model_config = ConfigDict(extra="forbid")

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


class Story(ApiModel):
    """A ranked story snapshot with its attribution sources."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    rank: int = Field(ge=1, le=8)
    title: str
    summary: str
    why_it_matters: str
    category: Category
    region: Region
    direction: Direction
    impact: int = Field(ge=1, le=5)
    content_basis: ContentBasis
    derivative_license: str | None
    derivative_license_url: str | None
    modification_notice: str | None
    sources: list[StorySource]


class StoryCollection(ApiModel):
    """The stories of one published report, optionally filtered."""

    model_config = ConfigDict(extra="forbid")

    date: date
    stories: list[Story]
