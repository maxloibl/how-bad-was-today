from pathlib import Path
from typing import Any

import pytest
import yaml

from daily_signal.infrastructure.db.seed import (
    PermissionDefaults,
    SourceConfig,
    SourceConfigError,
    SourcesConfig,
    load_sources_config,
    seed_sources,
)

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


def _source(**overrides: Any) -> dict[str, Any]:
    source: dict[str, Any] = {
        "slug": "global-voices",
        "name": "Global Voices",
        "publisher_group_id": "stichting-global-voices",
        "publisher_group_name": "Stichting Global Voices",
        "homepage_url": "https://globalvoices.org/",
        "origin_country": "NL",
        "primary_language": "en",
        "source_type": "editorial",
        "license_code": "CC-BY-3.0",
        "license_url": "https://creativecommons.org/licenses/by/3.0/",
        "terms_url": "https://globalvoices.org/about/",
        "content_scope": "scope",
        "attribution_requirements": "attribution",
        "feed_url": "https://globalvoices.org/feed/",
        "review_status": "in_review",
        "enabled": False,
        "permissions_approved": False,
    }
    source.update(overrides)
    return source


@pytest.mark.parametrize(
    "doc",
    [
        yaml.safe_dump(
            {
                "version": 1,
                "sources": [],
                "permission_defaults": {"review_status": "approved"},
            }
        ),
        yaml.safe_dump(
            {
                "version": 1,
                "sources": [],
                "permission_defaults": {
                    "review_status": "in_review",
                    "publish_derivatives": True,
                },
            }
        ),
        yaml.safe_dump(
            {
                "version": 1,
                "sources": [_source(enabled=True)],
                "permission_defaults": {"review_status": "in_review"},
            }
        ),
        yaml.safe_dump(
            {
                "version": 1,
                "sources": [_source(permissions_approved=True)],
                "permission_defaults": {"review_status": "in_review"},
            }
        ),
        yaml.safe_dump(
            {
                "version": 2,
                "sources": [],
                "permission_defaults": {"review_status": "in_review"},
            }
        ),
    ],
    ids=[
        "defaults_review_status",
        "defaults_flag",
        "source_enabled",
        "source_permissions_approved",
        "version",
    ],
)
def test_rejects_a_config_that_grants_rights(tmp_path: Path, doc: str) -> None:
    bad = tmp_path / "sources.yaml"
    bad.write_text(doc, encoding="utf-8")
    with pytest.raises(SourceConfigError):
        load_sources_config(bad)


class _UnusedSession:
    """A stand-in session that fails loudly if the seed touches it.

    The rights lock must reject a violating config before any query or insert,
    so ``seed_sources`` should never call into the session in this test.
    """

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"seed_sources touched the session ({name}) before the guard")


async def test_seed_sources_rejects_granted_rights_before_touching_session() -> None:
    # Include a real source so that, without the guard, the seed would call into
    # the session. The rights lock must fire before any query or insert.
    config = SourcesConfig(
        version=1,
        sources=(SourceConfig(**_source()),),
        permission_defaults=PermissionDefaults(publish_derivatives=True),
    )
    with pytest.raises(SourceConfigError):
        await seed_sources(_UnusedSession(), config)  # type: ignore[arg-type]
