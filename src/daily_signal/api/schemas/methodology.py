"""Methodology DTO matching ``contracts/openapi.yaml``."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from daily_signal.api.schemas.base import ApiModel
from daily_signal.application.methodology import MethodologyConfig

#: Score-band colours must be six-digit hex values prefixed with ``#``.
_HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"


class ScoreColors(BaseModel):
    """The five score-band colours, keyed by the contract's band labels.

    The keys stay snake_case, so this model deliberately does *not* use the
    camelCase ``ApiModel`` alias generator.
    """

    model_config = ConfigDict(extra="forbid")

    very_negative: str = Field(pattern=_HEX_COLOR)
    negative: str = Field(pattern=_HEX_COLOR)
    mixed: str = Field(pattern=_HEX_COLOR)
    positive: str = Field(pattern=_HEX_COLOR)
    very_positive: str = Field(pattern=_HEX_COLOR)


class Methodology(ApiModel):
    """The versioned public scoring and attribution methodology."""

    model_config = ConfigDict(extra="forbid")

    version: str
    timezone: Literal["Europe/Berlin"]
    score_scale: Literal[5]
    relevance_weights: dict[str, Annotated[int, Field(ge=0, le=100)]]
    score_thresholds: list[float]
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
        score_colors=ScoreColors(
            very_negative=config.score_colors.very_negative,
            negative=config.score_colors.negative,
            mixed=config.score_colors.mixed,
            positive=config.score_colors.positive,
            very_positive=config.score_colors.very_positive,
        ),
        description=config.description,
    )
