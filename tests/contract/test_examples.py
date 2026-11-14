import json
from pathlib import Path

import pytest

from daily_signal.domain.enums import DayLabel, Direction
from daily_signal.domain.scoring import ScoredStory, compute_day_score
from tests.contract.validation import assert_valid

ROOT = Path(__file__).resolve().parents[2]
DIRECTION_VALUES = [-2, 0, 2, -1, 1]


def test_api_error_example_matches_contract() -> None:
    example = json.loads((ROOT / "contracts/examples/api-error.json").read_text(encoding="utf-8"))
    assert_valid(example, "ApiError")


def test_daily_report_example_matches_contract() -> None:
    example = json.loads(
        (ROOT / "contracts/examples/daily-report.json").read_text(encoding="utf-8")
    )
    assert_valid(example, "DailyReport")


def test_daily_report_example_score_matches_compute_day_score() -> None:
    example = json.loads(
        (ROOT / "contracts/examples/daily-report.json").read_text(encoding="utf-8")
    )
    stories = example["stories"]
    assert len(stories) == len(DIRECTION_VALUES)
    scored = [
        ScoredStory(Direction(story["direction"]), value, story["impact"])
        for story, value in zip(stories, DIRECTION_VALUES, strict=True)
    ]

    result = compute_day_score(scored)

    assert result.raw_value == pytest.approx(example["score"]["rawValue"])
    assert result.value == example["score"]["value"]
    assert result.label is DayLabel(example["score"]["label"])
