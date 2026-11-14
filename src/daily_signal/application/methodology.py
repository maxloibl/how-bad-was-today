"""Load and validate the pinned public scoring methodology.

The methodology document (``config/methodology.yaml``) is the single source of
the values served by ``GET /v1/methodology``. :func:`load_methodology` fails
closed on any malformed document: unknown keys, a non-``Europe/Berlin``
timezone, a score scale other than 5, a threshold count other than four, a
missing or extra score colour, or a colour that is not a ``#RRGGBB`` hex value.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

#: Score-band colours must be six-digit hex values prefixed with ``#``.
_HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"

#: Number of cutoffs separating the five score bands.
_THRESHOLD_COUNT = 4


class MethodologyConfigError(ValueError):
    """Raised when the methodology configuration is malformed."""


class ScoreColors(BaseModel):
    """The five exact score-band colours, keyed by label."""

    model_config = ConfigDict(extra="forbid")

    very_negative: str = Field(pattern=_HEX_COLOR)
    negative: str = Field(pattern=_HEX_COLOR)
    mixed: str = Field(pattern=_HEX_COLOR)
    positive: str = Field(pattern=_HEX_COLOR)
    very_positive: str = Field(pattern=_HEX_COLOR)


class MethodologyConfig(BaseModel):
    """Validated public methodology document."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    timezone: Literal["Europe/Berlin"]
    score_scale: Literal[5]
    relevance_weights: dict[str, Annotated[int, Field(ge=0, le=100)]]
    score_thresholds: list[float] = Field(min_length=_THRESHOLD_COUNT, max_length=_THRESHOLD_COUNT)
    score_colors: ScoreColors
    description: str = Field(min_length=1)

    @field_validator("relevance_weights")
    @classmethod
    def _require_impact_weight(cls, value: dict[str, int]) -> dict[str, int]:
        """Fail closed unless the mandatory ``impact`` weight is present."""
        if "impact" not in value:
            raise ValueError("relevance_weights must include an 'impact' weight")
        return value


def load_methodology(path: Path) -> MethodologyConfig:
    """Load and validate the methodology document at ``path``.

    Raises :class:`MethodologyConfigError` when the file cannot be read, is not
    a YAML mapping, or fails validation.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MethodologyConfigError(f"cannot read methodology config {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise MethodologyConfigError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise MethodologyConfigError(f"{path}: expected a top-level YAML mapping")

    try:
        return MethodologyConfig.model_validate(raw)
    except ValidationError as exc:
        raise MethodologyConfigError(f"{path}: {exc}") from exc
