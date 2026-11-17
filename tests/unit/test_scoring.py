import pytest

from daily_signal.domain.enums import DayLabel, Direction
from daily_signal.domain.scoring import (
    NoScorableStoriesError,
    ScoredStory,
    compute_day_score,
    score_from_raw,
)


@pytest.mark.parametrize(
    ("raw", "value"),
    [
        (-2.0, 1),
        (-1.1001, 1),
        (-1.1, 2),
        (-0.3001, 2),
        (-0.3, 3),
        (0.0, 3),
        (0.3, 3),
        (0.3001, 4),
        (1.1, 4),
        (1.1001, 5),
        (2.0, 5),
    ],
)
def test_threshold_boundaries(raw: float, value: int) -> None:
    assert score_from_raw(raw).value == value


@pytest.mark.parametrize("raw", [2.0001, -2.0001, float("nan")])
def test_score_from_raw_rejects_out_of_range_values(raw: float) -> None:
    with pytest.raises(ValueError, match="raw score must be between"):
        score_from_raw(raw)


def test_scorable_direction_without_value_raises() -> None:
    with pytest.raises(ValueError, match="must have a direction value"):
        compute_day_score([ScoredStory(Direction.NEGATIVE, None, 2)])


def test_impact_squared_weighting() -> None:
    result = compute_day_score(
        [
            ScoredStory(Direction.NEGATIVE, -2, 2),
            ScoredStory(Direction.POSITIVE, 2, 1),
        ]
    )
    assert result.raw_value == pytest.approx(-1.2)
    assert result.value == 1
    assert result.label is DayLabel.VERY_NEGATIVE


def test_mixed_and_unknown_are_excluded() -> None:
    result = compute_day_score(
        [
            ScoredStory(Direction.MIXED, None, 5),
            ScoredStory(Direction.UNKNOWN, None, 5),
            ScoredStory(Direction.NEUTRAL, 0, 1),
        ]
    )
    assert result.raw_value == 0.0
    assert result.value == 3


def test_no_scorable_stories_raises() -> None:
    with pytest.raises(NoScorableStoriesError):
        compute_day_score([ScoredStory(Direction.UNKNOWN, None, 3)])
