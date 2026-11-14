from pathlib import Path
from typing import Any

import pytest
import yaml

from daily_signal.application.methodology import MethodologyConfigError, load_methodology

ROOT = Path(__file__).resolve().parents[2]

_COLORS: dict[str, str] = {
    "very_negative": "#CF6666",
    "negative": "#DE9A57",
    "mixed": "#B8AC69",
    "positive": "#85B78A",
    "very_positive": "#43A779",
}


def test_loads_pinned_methodology() -> None:
    config = load_methodology(ROOT / "config/methodology.yaml")
    assert config.version == "1.0.0"
    assert config.timezone == "Europe/Berlin"
    assert config.score_scale == 5
    assert config.relevance_weights == {"impact": 100}
    assert config.score_thresholds == [-1.1, -0.3, 0.3, 1.1]
    assert config.score_colors.very_negative == "#CF6666"
    assert config.score_colors.negative == "#DE9A57"
    assert config.score_colors.mixed == "#B8AC69"
    assert config.score_colors.positive == "#85B78A"
    assert config.score_colors.very_positive == "#43A779"
    assert config.description


def _doc(**overrides: Any) -> str:
    doc: dict[str, Any] = {
        "version": "1.0.0",
        "timezone": "Europe/Berlin",
        "score_scale": 5,
        "relevance_weights": {"impact": 100},
        "score_thresholds": [-1.1, -0.3, 0.3, 1.1],
        "score_colors": dict(_COLORS),
        "description": "Factual description.",
    }
    doc.update(overrides)
    return yaml.safe_dump(doc)


@pytest.mark.parametrize(
    "doc",
    [
        _doc(unknown_key=True),
        _doc(score_thresholds=[-1.1, -0.3, 0.3]),
        _doc(score_thresholds=[-1.1, -0.3, 0.3, 1.1, 2.0]),
        _doc(relevance_weights={}),
        _doc(score_colors={**_COLORS, "mixed": "#B8AC6"}),
        _doc(score_colors={key: value for key, value in _COLORS.items() if key != "mixed"}),
        _doc(score_colors={**_COLORS, "neutral": "#000000"}),
        _doc(version=""),
        _doc(description=""),
    ],
    ids=[
        "unknown_key",
        "three_thresholds",
        "five_thresholds",
        "missing_impact_weight",
        "malformed_hex",
        "missing_color",
        "extra_color",
        "empty_version",
        "empty_description",
    ],
)
def test_rejects_malformed_methodology(tmp_path: Path, doc: str) -> None:
    bad = tmp_path / "methodology.yaml"
    bad.write_text(doc, encoding="utf-8")
    with pytest.raises(MethodologyConfigError):
        load_methodology(bad)


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(MethodologyConfigError):
        load_methodology(tmp_path / "does-not-exist.yaml")


def test_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    bad = tmp_path / "methodology.yaml"
    bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(MethodologyConfigError):
        load_methodology(bad)
