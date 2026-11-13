from pathlib import Path

import pytest

from daily_signal.infrastructure.db.seed import SourceConfigError, load_sources_config

ROOT = Path(__file__).resolve().parents[2]


def test_loads_three_in_review_sources() -> None:
    config = load_sources_config(ROOT / "config/sources.yaml")
    assert len(config.sources) == 3
    assert {source.slug for source in config.sources} == {
        "global-voices",
        "netzpolitik-org",
        "el-salto",
    }
    assert all(source.review_status == "in_review" for source in config.sources)
    assert all(source.enabled is False for source in config.sources)


def test_rejects_a_config_that_grants_rights(tmp_path: Path) -> None:
    bad = tmp_path / "sources.yaml"
    bad.write_text(
        "version: 1\nsources: []\npermission_defaults: {review_status: approved}\n",
        encoding="utf-8",
    )
    with pytest.raises(SourceConfigError):
        load_sources_config(bad)
