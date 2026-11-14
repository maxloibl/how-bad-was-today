"""Methodology DTO matching ``contracts/openapi.yaml``."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import ConfigDict, Field

from daily_signal.api.schemas.base import ApiModel
from daily_signal.application.methodology import MethodologyConfig, ScoreColors

#: Number of cutoffs separating the five score bands.
_THRESHOLD_COUNT = 4


class Methodology(ApiModel):
    """The versioned public scoring and attribution methodology.

    ``ScoreColors`` is reused from the application layer: its keys are the
    contract's snake_case band labels, so it is already wire-compatible.
    """

    model_config = ConfigDict(extra="forbid")

    version: str
    timezone: Literal["Europe/Berlin"]
    score_scale: Literal[5]
    relevance_weights: dict[str, Annotated[int, Field(ge=0, le=100)]]
    score_thresholds: list[float] = Field(min_length=_THRESHOLD_COUNT, max_length=_THRESHOLD_COUNT)
    score_colors: ScoreColors
    description: str


def methodology(config: MethodologyConfig) -> Methodology:
    """Build the methodology DTO from the validated configuration."""
    return Methodology(
        version=config.version,
        timezone=config.timezone,
        score_scale=config.score_scale,
        relevance_weights=config.relevance_weights,
        score_thresholds=config.score_thresholds,
        score_colors=config.score_colors,
        description=config.description,
    )
