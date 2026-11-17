import json
from collections.abc import Iterator

import pytest

from daily_signal.cli import main
from daily_signal.core.config import get_settings

pytestmark = pytest.mark.integration


@pytest.fixture
def isolated_settings_cache() -> Iterator[None]:
    """Keep a test-only DATABASE_URL out of the process-wide settings cache."""
    get_settings.cache_clear()
    try:
        yield
    finally:
        get_settings.cache_clear()


def test_seed_sources_cli_returns_0(
    migrated_database: str, monkeypatch, capsys, isolated_settings_cache: None
) -> None:
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    get_settings.cache_clear()

    exit_code = main(["seed-sources", "--config", "config/sources.yaml"])

    assert exit_code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["created"] >= 0
    assert summary["skipped"] >= 0
    assert summary["created"] + summary["skipped"] == 3
