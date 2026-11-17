"""The public DTOs must enforce the bounds pinned by ``contracts/openapi.yaml``."""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from daily_signal.api.schemas.days import DayScore, DaySummary
from daily_signal.api.schemas.stories import Story

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE: dict[str, Any] = json.loads(
    (ROOT / "contracts/examples/daily-report.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("field", "value"),
    [("value", 0), ("value", 6), ("rawValue", -2.1), ("rawValue", 2.1), ("explanation", "")],
)
def test_day_score_enforces_contract_bounds(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        DayScore.model_validate({**EXAMPLE["score"], field: value})


@pytest.mark.parametrize("story_count", [4, 9])
def test_day_summary_story_count_enforces_contract_bounds(story_count: int) -> None:
    with pytest.raises(ValidationError):
        DaySummary.model_validate({**EXAMPLE, "storyCount": story_count})


@pytest.mark.parametrize(
    ("field", "value"),
    [("rank", 0), ("rank", 9), ("impact", 0), ("impact", 6)],
)
def test_story_enforces_contract_bounds(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        Story.model_validate({**EXAMPLE["stories"][0], field: value})
