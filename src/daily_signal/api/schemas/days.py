"""Day and daily-report DTOs matching ``contracts/openapi.yaml``."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import ConfigDict, Field

from daily_signal.api.schemas.base import ApiModel
from daily_signal.api.schemas.stories import Story
from daily_signal.domain.enums import Confidence, DayLabel


class DayScore(ApiModel):
    """The published 1-5 day score with its raw weighted mean."""

    model_config = ConfigDict(extra="forbid")

    value: int = Field(ge=1, le=5)
    max: Literal[5] = 5
    label: DayLabel
    raw_value: float = Field(ge=-2, le=2)
    confidence: Confidence
    explanation: str = Field(min_length=1)


class DaySummary(ApiModel):
    """Calendar-level summary of one published day."""

    date: date
    score: DayScore
    headline: str
    story_count: int = Field(ge=5, le=8)
    revision: int
    published_at: datetime


class DailyReport(DaySummary):
    """A full published daily report including its stories."""

    timezone: Literal["Europe/Berlin"]
    summary: str
    methodology_version: str
    stories: list[Story]


class DayCollection(ApiModel):
    """Published days within an inclusive calendar range."""

    model_config = ConfigDict(extra="forbid")

    from_: date = Field(alias="from")
    to: date
    days: list[DaySummary]
