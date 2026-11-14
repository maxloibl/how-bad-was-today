import json
from pathlib import Path

from tests.contract.validation import assert_valid

ROOT = Path(__file__).resolve().parents[2]


def test_api_error_example_matches_contract() -> None:
    example = json.loads((ROOT / "contracts/examples/api-error.json").read_text(encoding="utf-8"))
    assert_valid(example, "ApiError")


def test_daily_report_example_matches_contract() -> None:
    example = json.loads(
        (ROOT / "contracts/examples/daily-report.json").read_text(encoding="utf-8")
    )
    assert_valid(example, "DailyReport")
