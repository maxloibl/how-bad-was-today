from pathlib import Path

import yaml
from openapi_spec_validator import validate_spec

ROOT = Path(__file__).resolve().parents[2]


def test_openapi_contract_is_valid_and_complete() -> None:
    spec = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text(encoding="utf-8"))
    validate_spec(spec)
    assert set(spec["paths"]) == {
        "/v1/days",
        "/v1/days/latest",
        "/v1/days/{date}",
        "/v1/days/{date}/stories",
        "/v1/stories/{id}",
        "/v1/sources",
        "/v1/methodology",
        "/health/live",
        "/health/ready",
    }
    methods = {method for path in spec["paths"].values() for method in path}
    assert methods == {"get"}


def test_seed_sources_are_disabled_and_in_review() -> None:
    config = yaml.safe_load((ROOT / "config/sources.yaml").read_text(encoding="utf-8"))
    assert config["version"] == 1
    assert len(config["sources"]) == 3
    for source in config["sources"]:
        assert source["review_status"] == "in_review"
        assert source["enabled"] is False
        assert source["permissions_approved"] is False
    assert all(
        value is False
        for value in config["permission_defaults"].values()
        if isinstance(value, bool)
    )
