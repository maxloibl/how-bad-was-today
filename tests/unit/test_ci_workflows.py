from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_ci_runs_all_required_checks() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["test"]["steps"]
    commands = "\n".join(str(step.get("run", "")) for step in steps)
    assert "uv sync --locked" in commands
    assert "ruff check" in commands
    assert "ruff format --check" in commands
    assert "mypy src" in commands
    assert "pytest" in commands
    assert workflow["jobs"]["test"]["services"]["postgres"]["image"].startswith("postgres:17")


def test_container_workflow_builds_without_pushing() -> None:
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/container.yml").read_text(encoding="utf-8")
    )
    steps = workflow["jobs"]["build"]["steps"]
    build = next(step for step in steps if "build-push-action" in str(step.get("uses", "")))
    assert build["with"]["push"] is False
