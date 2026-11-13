"""Day score computation.

The day score is the impact-squared weighted mean of the story direction
values over ``negative``, ``neutral`` and ``positive`` stories. ``mixed`` and
``unknown`` stories carry no direction value and are excluded.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from daily_signal.domain.enums import DayLabel, Direction

_MIN_RAW = -2.0
_MAX_RAW = 2.0

_SCORABLE_DIRECTIONS = frozenset({Direction.NEGATIVE, Direction.NEUTRAL, Direction.POSITIVE})

_LABELS_BY_VALUE: dict[int, DayLabel] = {
    1: DayLabel.VERY_NEGATIVE,
    2: DayLabel.NEGATIVE,
    3: DayLabel.MIXED,
    4: DayLabel.POSITIVE,
    5: DayLabel.VERY_POSITIVE,
}


class NoScorableStoriesError(ValueError):
    """Raised when no story can contribute to a day score."""


@dataclass(frozen=True)
class ScoredStory:
    """Direction and impact of a single story as needed for scoring."""

    direction: Direction
    direction_value: int | None
    impact: int


@dataclass(frozen=True)
class DayScore:
    """A computed 1-5 day score together with its raw weighted mean."""

    value: int
    raw_value: float
    label: DayLabel


def score_from_raw(raw: float) -> DayScore:
    """Map a raw weighted mean in ``[-2, 2]`` to a 1-5 day score."""
    if not _MIN_RAW <= raw <= _MAX_RAW:
        raise ValueError(f"raw score must be between {_MIN_RAW} and {_MAX_RAW}, got {raw}")

    if raw < -1.1:
        value = 1
    elif raw < -0.3:
        value = 2
    elif raw <= 0.3:
        value = 3
    elif raw <= 1.1:
        value = 4
    else:
        value = 5

    return DayScore(value=value, raw_value=float(raw), label=_LABELS_BY_VALUE[value])


def compute_day_score(stories: Sequence[ScoredStory]) -> DayScore:
    """Compute the weighted day score from the scorable stories."""
    weighted_sum = 0
    weight_total = 0

    for story in stories:
        if story.direction not in _SCORABLE_DIRECTIONS:
            continue
        if story.direction_value is None:
            raise ValueError(f"{story.direction.value} story must have a direction value")
        weight = story.impact**2
        weighted_sum += story.direction_value * weight
        weight_total += weight

    if weight_total == 0:
        raise NoScorableStoriesError("at least one scorable story is required")

    return score_from_raw(weighted_sum / weight_total)
