# Daily Signal Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the runnable, contract-first foundation of Daily Signal: PostgreSQL schema, read-only FastAPI v1 API, source seeding, runtime processes, Docker Compose, and CI.

**Architecture:** Modular monolith in one Python package. API, worker, and scheduler share the codebase and image but run as separate processes. The hand-written OpenAPI 3.1 contract under `contracts/` is authoritative; FastAPI responses are validated against it. PostgreSQL is managed exclusively through Alembic migrations.

**Tech Stack:** Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2 async, asyncpg, Alembic, PostgreSQL 17, uv, Docker Compose, pytest, ruff, mypy.

**Spec:** `docs/specs/daily-signal-v1.0/README.md`, `schema.sql`, `openapi.yaml`, `repository-structure.md`, `sources.yaml` (all in the same directory).

## Global Constraints

- Python 3.13; FastAPI; Pydantic 2; SQLAlchemy 2; Alembic; PostgreSQL 17+.
- Dependency management with `uv`; `uv.lock` is committed; `uv sync --locked` must work.
- Public API is read-only under `/v1`; no public admin, job, prompt, or source-approval endpoints.
- Only rows with `daily_reports.status='published' AND is_current=true` are publicly visible.
- `Story.id` identifies a report-story snapshot, not a source article or cross-day event.
- Report days are `Europe/Berlin` calendar dates; all database timestamps are UTC-aware `TIMESTAMPTZ`.
- Unpublished days are omitted from `/v1/days`; they never receive a neutral score of 3.
- 5–8 stories per report, complete QA, and confidence `high`/`medium` are enforced by the publication workflow, not by SQL row-count checks.
- Day score: weighted mean of `direction_value * impact^2` over `negative`, `neutral`, `positive`; `mixed`/`unknown` excluded. Thresholds: `< -1.1 → 1`, `[-1.1,-0.3) → 2`, `[-0.3,0.3] → 3`, `(0.3,1.1] → 4`, `> 1.1 → 5`.
- Score colors exactly: `#CF6666`, `#DE9A57`, `#B8AC69`, `#85B78A`, `#43A779`.
- `GET /v1/days` accepts at most 366 inclusive calendar days and requires `from <= to`.
- All three seed sources stay `in_review`, `enabled=false`, with every permission flag `false`; no environment-variable switch may bypass this.
- No raw article text, prompts, or third-party full texts in logs.
- No browser-search ingestion pipeline; only documented official feeds/APIs later.
- Schema changes only through Alembic; the API never auto-creates tables. `schema.sql` is a reference only.
- Register `/v1/days/latest` before `/v1/days/{date}`.
- Scheduler ticks every 15 minutes; daily analysis may start after 03:30 Europe/Berlin; DB lock and catch-up semantics prevent duplicate work.
- Compose services: `api`, `worker`, `scheduler`, `db`; PostgreSQL has no host port in production.
- CI runs linting, type checking, tests, migration check, and API contract checks.

## Review Focus

1. **Invalid date input** — `from > to`, ranges over 366 days, and malformed dates must return the documented `400`/`422` error envelope, never a `500`.
2. **Conditional requests** — `If-None-Match` with one tag, multiple tags, weak tags, or no header must yield `304` only on a match, otherwise `200`.
3. **Revision visibility** — superseded, draft, validated, withdrawn, or non-current reports and their stories must never appear on any public endpoint.
4. **Source clearance** — unapproved or disabled sources, and sources whose latest permission revision is not approved, must never appear in `/v1/sources`; seeding must not enable them.
5. **Empty database and unavailable database** — empty calendar returns `days: []`, latest returns `404`, sources returns `[]`; readiness returns `503` instead of crashing when PostgreSQL is unreachable.

## Target File Structure

```text
.github/workflows/{ci.yml,container.yml}
config/{sources.yaml,methodology.yaml}
contracts/{openapi.yaml,examples/{daily-report.json,api-error.json}}
docker/initdb/01-test-database.sql
docs/{architecture.md,data-model.md,source-policy.md,scoring-methodology.md,adr/0001-modular-monolith.md}
docs/specs/daily-signal-v1.0/{README.md,schema.sql,openapi.yaml,repository-structure.md,sources.yaml}
migrations/{env.py,script.py.mako,versions/0001_initial.py}
src/daily_signal/
  main.py cli.py
  api/{dependencies.py,errors.py,middleware.py,etag.py}
  api/schemas/{base.py,days.py,stories.py,sources.py,methodology.py,errors.py,health.py}
  api/v1/{router.py,days.py,stories.py,sources.py,methodology.py}
  domain/{enums.py,scoring.py,licensing.py}
  application/ports/repositories.py
  application/queries/{get_daily_report.py,list_daily_reports.py}
  application/methodology.py
  infrastructure/db/{base.py,models.py,session.py,seed.py,locks.py}
  infrastructure/db/repositories/{reports.py,sources.py}
  jobs/{worker.py,scheduler.py}
  core/{config.py,logging.py,clock.py}
tests/
  conftest.py
  unit/{test_package.py,test_scoring.py,test_rights.py,test_models_metadata.py,test_clock.py,test_sources_config.py,test_scheduler.py,test_ci_workflows.py}
  integration/{test_migrations.py,test_seed.py,test_api_health.py,test_api_reports.py,test_api_sources.py,test_advisory_lock.py}
  contract/{test_contract_files.py,test_examples.py,validation.py}
  fixtures/factories.py
.dockerignore .env.example .gitattributes .gitignore .python-version
alembic.ini compose.yaml compose.dev.yaml Dockerfile pyproject.toml uv.lock README.md
```

---

### Task 1: Scaffolding, tooling, and authoritative contracts

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.gitignore`, `.dockerignore`, `.gitattributes`, `.env.example`
- Create: `src/daily_signal/__init__.py`, `tests/__init__.py`, `tests/unit/__init__.py`, `tests/contract/__init__.py`, `tests/unit/test_package.py`, `tests/contract/test_contract_files.py`
- Create: `contracts/openapi.yaml` (byte-identical copy of `docs/specs/daily-signal-v1.0/openapi.yaml`)
- Create: `config/sources.yaml` (byte-identical copy of `docs/specs/daily-signal-v1.0/sources.yaml`)
- Create: `contracts/examples/api-error.json`

**Interfaces:**
- Produces: `daily_signal.__version__ == "0.1.0"`.
- Produces: canonical paths `contracts/openapi.yaml`, `config/sources.yaml`, `config/methodology.yaml` (the last is added in Task 8).
- Produces: runnable commands `uv sync --locked`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_package.py
import daily_signal


def test_package_version() -> None:
    assert daily_signal.__version__ == "0.1.0"
```

```python
# tests/contract/test_contract_files.py
from pathlib import Path

import yaml
from openapi_spec_validator import validate_spec

ROOT = Path(__file__).resolve().parents[2]


def test_openapi_contract_is_valid_and_complete() -> None:
    spec = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text(encoding="utf-8"))
    validate_spec(spec)
    assert set(spec["paths"]) == {
        "/v1/days", "/v1/days/latest", "/v1/days/{date}", "/v1/days/{date}/stories",
        "/v1/stories/{id}", "/v1/sources", "/v1/methodology",
        "/health/live", "/health/ready",
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
    assert all(value is False for value in config["permission_defaults"].values() if isinstance(value, bool))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/test_package.py tests/contract/test_contract_files.py -v`
Expected: FAIL with import/file-not-found errors.

- [ ] **Step 3: Create the project configuration and copy the contracts**

`pyproject.toml` must declare `requires-python = ">=3.13"`, the hatchling build backend with `packages = ["src/daily_signal"]`, and these runtime dependencies: `alembic`, `asyncpg`, `fastapi`, `pydantic`, `pydantic-settings`, `pyyaml`, `sqlalchemy[asyncio]`, `uvicorn[standard]`. Dev group: `asgi-lifespan`, `httpx`, `jsonschema`, `mypy`, `openapi-spec-validator`, `pytest`, `pytest-asyncio`, `referencing`, `ruff`, `types-pyyaml`. Configure pytest with `asyncio_mode = "auto"`, `testpaths = ["tests"]`, marker `integration`; ruff with `target-version = "py313"`, `line-length = 100`; mypy with `python_version = "3.13"`, `strict = true`, `mypy_path = "src"`.

Write `__version__ = "0.1.0"` in `src/daily_signal/__init__.py`. Copy the two spec files with `Copy-Item` (do not retype them). Add `.env.example` with `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `LOG_LEVEL`, `RATE_LIMIT_PER_MINUTE`, `SCHEDULER_TICK_SECONDS`, `CORS_ORIGINS`. Add `.gitattributes` containing `* text=auto eol=lf` and `*.sh text eol=lf`. Ignore `.venv/`, `__pycache__/`, `.env`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.superpowers/`.

- [ ] **Step 4: Lock, sync, and verify**

Run:

```powershell
uv lock
uv sync --locked
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest tests/unit/test_package.py tests/contract/test_contract_files.py -v
```

Expected: all commands exit 0; both tests pass.

- [ ] **Step 5: Commit**

```powershell
git add pyproject.toml uv.lock .python-version .gitignore .dockerignore .gitattributes .env.example src tests contracts config docs/specs
git commit -m "chore: scaffold project and add authoritative contracts"
```

---

### Task 2: Domain enums, scoring, and licensing rules

**Files:**
- Create: `src/daily_signal/domain/__init__.py`, `src/daily_signal/domain/enums.py`, `src/daily_signal/domain/scoring.py`, `src/daily_signal/domain/licensing.py`
- Create: `tests/unit/test_scoring.py`, `tests/unit/test_rights.py`

**Interfaces:**
- Produces: `DayLabel`, `Direction`, `Confidence`, `Category`, `Region`, `ContentBasis`, `ReviewStatus`, `SourceType` (all `StrEnum` with the exact lowercase values from the contract/schema).
- Produces: `ScoredStory(direction: Direction, direction_value: int | None, impact: int)`, `DayScore(value: int, raw_value: float, label: DayLabel)`.
- Produces: `score_from_raw(raw: float) -> DayScore`; `compute_day_score(stories: Sequence[ScoredStory]) -> DayScore`; `NoScorableStoriesError(ValueError)`.
- Produces: `PermissionProfile(review_status, analyze_content, create_adaptations, publish_derivatives, send_to_external_llm, fetch_full_text)`, `ItemRights(license_verified, contains_third_party_material)`, `assert_can_publish(permission, item, content_basis, *, uses_external_llm=False, uses_full_text=False) -> None`, `RightsError(ValueError)`.

- [ ] **Step 1: Write the failing scoring tests**

```python
# tests/unit/test_scoring.py
import pytest

from daily_signal.domain.enums import DayLabel, Direction
from daily_signal.domain.scoring import (
    NoScorableStoriesError, ScoredStory, compute_day_score, score_from_raw,
)


@pytest.mark.parametrize(
    ("raw", "value"),
    [(-2.0, 1), (-1.1001, 1), (-1.1, 2), (-0.3001, 2), (-0.3, 3),
     (0.0, 3), (0.3, 3), (0.3001, 4), (1.1, 4), (1.1001, 5), (2.0, 5)],
)
def test_threshold_boundaries(raw: float, value: int) -> None:
    assert score_from_raw(raw).value == value


def test_impact_squared_weighting() -> None:
    result = compute_day_score([
        ScoredStory(Direction.NEGATIVE, -2, 2),
        ScoredStory(Direction.POSITIVE, 2, 1),
    ])
    assert result.raw_value == pytest.approx(-1.2)
    assert result.value == 1
    assert result.label is DayLabel.VERY_NEGATIVE


def test_mixed_and_unknown_are_excluded() -> None:
    result = compute_day_score([
        ScoredStory(Direction.MIXED, None, 5),
        ScoredStory(Direction.UNKNOWN, None, 5),
        ScoredStory(Direction.NEUTRAL, 0, 1),
    ])
    assert result.raw_value == 0.0
    assert result.value == 3


def test_no_scorable_stories_raises() -> None:
    with pytest.raises(NoScorableStoriesError):
        compute_day_score([ScoredStory(Direction.UNKNOWN, None, 3)])
```

- [ ] **Step 2: Write the failing rights tests**

```python
# tests/unit/test_rights.py
import pytest

from daily_signal.domain.enums import ContentBasis, ReviewStatus
from daily_signal.domain.licensing import (
    ItemRights, PermissionProfile, RightsError, assert_can_publish,
)

APPROVED = PermissionProfile(
    review_status=ReviewStatus.APPROVED, analyze_content=True, create_adaptations=True,
    publish_derivatives=True, send_to_external_llm=True, fetch_full_text=True,
)
CLEARED = ItemRights(license_verified=True, contains_third_party_material=False)


def test_approved_facts_synthesis_is_allowed() -> None:
    assert_can_publish(APPROVED, CLEARED, ContentBasis.FACTS_SYNTHESIS)


def test_in_review_source_is_rejected() -> None:
    profile = PermissionProfile(**{**APPROVED.__dict__, "review_status": ReviewStatus.IN_REVIEW})
    with pytest.raises(RightsError, match="approved"):
        assert_can_publish(profile, CLEARED, ContentBasis.FACTS_SYNTHESIS)


def test_unverified_or_third_party_item_is_rejected() -> None:
    with pytest.raises(RightsError, match="verified"):
        assert_can_publish(APPROVED, ItemRights(False, False), ContentBasis.FACTS_SYNTHESIS)
    with pytest.raises(RightsError, match="third-party"):
        assert_can_publish(APPROVED, ItemRights(True, True), ContentBasis.FACTS_SYNTHESIS)


def test_adaptation_requires_adaptation_permission() -> None:
    profile = PermissionProfile(**{**APPROVED.__dict__, "create_adaptations": False})
    with pytest.raises(RightsError, match="adaptation"):
        assert_can_publish(profile, CLEARED, ContentBasis.ADAPTATION)


def test_external_llm_and_full_text_require_their_flags() -> None:
    profile = PermissionProfile(**{**APPROVED.__dict__, "send_to_external_llm": False,
                                   "fetch_full_text": False})
    with pytest.raises(RightsError, match="external LLM"):
        assert_can_publish(profile, CLEARED, ContentBasis.FACTS_SYNTHESIS, uses_external_llm=True)
    with pytest.raises(RightsError, match="full text"):
        assert_can_publish(profile, CLEARED, ContentBasis.FACTS_SYNTHESIS, uses_full_text=True)
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/test_scoring.py tests/unit/test_rights.py -v`
Expected: FAIL with import errors.

- [ ] **Step 4: Implement the domain modules**

`score_from_raw` computes the weighted mean result for an already computed raw score: clamp/validate `-2 <= raw <= 2`, apply the exact threshold table, and return `DayScore`. `compute_day_score` filters to `negative`/`neutral`/`positive`, requires `direction_value` not `None`, computes `sum(value * impact**2) / sum(impact**2)`, and raises `NoScorableStoriesError` when nothing is eligible. Do not add more validation than the spec requires. `assert_can_publish` checks in this order: review status approved; item license verified; no third-party material; `publish_derivatives`; `analyze_content`; adaptation permission if `ContentBasis.ADAPTATION`; external LLM flag if requested; full-text flag if requested. Raise `RightsError` with the words the tests match.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/test_scoring.py tests/unit/test_rights.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/daily_signal/domain tests/unit/test_scoring.py tests/unit/test_rights.py
git commit -m "feat: add scoring and licensing domain rules"
```

---

### Task 3: Configuration, clock, logging, and SQLAlchemy models

**Files:**
- Create: `src/daily_signal/core/__init__.py`, `core/config.py`, `core/clock.py`, `core/logging.py`
- Create: `src/daily_signal/infrastructure/__init__.py`, `infrastructure/db/__init__.py`, `infrastructure/db/base.py`, `infrastructure/db/models.py`, `infrastructure/db/session.py`
- Create: `tests/unit/test_models_metadata.py`, `tests/unit/test_clock.py`, `tests/unit/test_config.py`

**Interfaces:**
- Produces: `Settings` (`database_url: str = "postgresql+asyncpg://daily_signal:daily_signal@localhost:5432/daily_signal"`, `app_env: str = "local"`, `log_level: str = "INFO"`, `rate_limit_per_minute: int = 120`, `scheduler_tick_seconds: int = 900`, `cors_origins: list[str] = []`, `sources_config_path: Path = Path("config/sources.yaml")`, `methodology_config_path: Path = Path("config/methodology.yaml")`), `get_settings() -> Settings`.
- Produces: `utc_now() -> datetime`, `berlin_now() -> datetime`, `berlin_today() -> date`, `daily_analysis_due(now: datetime) -> bool`.
- Produces: `Base`, `create_engine(settings) -> AsyncEngine`, `create_session_factory(engine) -> async_sessionmaker[AsyncSession]`.
- Produces: exactly 14 ORM tables whose names, columns, constraints, and indexes match `docs/specs/daily-signal-v1.0/schema.sql`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_models_metadata.py
from daily_signal.infrastructure.db.base import Base
from daily_signal.infrastructure.db import models  # noqa: F401  (registers models)


EXPECTED_TABLES = {
    "publisher_groups", "news_sources", "source_feeds", "source_permissions",
    "source_items", "source_item_content", "events", "event_items", "event_claims",
    "claim_evidence", "pipeline_runs", "daily_reports", "daily_report_stories",
    "story_sources",
}


def test_all_tables_are_declared() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_critical_constraints_and_indexes_exist() -> None:
    reports = Base.metadata.tables["daily_reports"]
    index_names = {index.name for index in reports.indexes}
    assert "uq_current_published_report_per_day" in index_names
    assert "ix_daily_reports_calendar" in index_names
    checks = {c.name for c in reports.constraints}
    assert "published_report_complete" in checks
    assert "current_report_is_published" in checks

    items = Base.metadata.tables["source_items"]
    assert "uq_source_items_external_id" in {i.name for i in items.indexes}
```

```python
# tests/unit/test_clock.py
from datetime import datetime
from zoneinfo import ZoneInfo

from daily_signal.core.clock import daily_analysis_due

BERLIN = ZoneInfo("Europe/Berlin")


def test_daily_analysis_not_due_before_0330() -> None:
    assert daily_analysis_due(datetime(2026, 11, 13, 3, 29, tzinfo=BERLIN)) is False


def test_daily_analysis_due_at_and_after_0330() -> None:
    assert daily_analysis_due(datetime(2026, 11, 13, 3, 30, tzinfo=BERLIN)) is True
    assert daily_analysis_due(datetime(2026, 11, 13, 4, 0, tzinfo=BERLIN)) is True


def test_daily_analysis_uses_berlin_time_across_dst() -> None:
    # 02:30 UTC is 03:30 CET on the winter date and 04:30 CEST on the summer date.
    assert daily_analysis_due(datetime(2026, 1, 15, 2, 30, tzinfo=ZoneInfo("UTC"))) is True
    assert daily_analysis_due(datetime(2026, 7, 15, 2, 30, tzinfo=ZoneInfo("UTC"))) is True
```

```python
# tests/unit/test_config.py
from daily_signal.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(database_url="postgresql+asyncpg://u:p@localhost/db")
    assert settings.rate_limit_per_minute == 120
    assert settings.scheduler_tick_seconds == 900
    assert settings.cors_origins == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/test_models_metadata.py tests/unit/test_clock.py tests/unit/test_config.py -v`
Expected: FAIL with import errors.

- [ ] **Step 3: Implement config, clock, logging, and models**

Implement `Settings` with `pydantic_settings.BaseSettings` and `@lru_cache` `get_settings()`. `daily_analysis_due` converts the supplied aware datetime to `Europe/Berlin` and returns `time() >= time(3, 30)`.

Implement the 14 tables by translating `docs/specs/daily-signal-v1.0/schema.sql` literally into SQLAlchemy 2 `Mapped[...]`/`mapped_column()` declarations. Use `Uuid(as_uuid=True)` for UUIDs with `default=uuid4`, `DateTime(timezone=True)` for `TIMESTAMPTZ`, `JSONB` for `quality_checks`, `Numeric(12, 6)`/`Numeric(5, 3)` for money/raw score, `CHAR(2)`, `SMALLINT`, and the exact `CheckConstraint`, `UniqueConstraint`, composite `ForeignKeyConstraint`, and partial `Index(..., postgresql_where=...)` expressions from the SQL. Keep constraint and index names exactly as in the reference. Use a `DeclarativeBase` with a stable naming convention for unnamed constraints.

Implement `create_engine` with `pool_pre_ping=True` and `connect_args={"timeout": 5}`. `create_session_factory` uses `expire_on_commit=False`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/test_models_metadata.py tests/unit/test_clock.py tests/unit/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/daily_signal/core src/daily_signal/infrastructure tests/unit/test_models_metadata.py tests/unit/test_clock.py tests/unit/test_config.py
git commit -m "feat: add config, clock, and full ORM schema"
```

---

### Task 4: Alembic initial migration and database test harness

**Files:**
- Create: `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_initial.py`
- Create: `tests/conftest.py`, `tests/integration/__init__.py`, `tests/integration/test_migrations.py`, `tests/fixtures/__init__.py`

**Interfaces:**
- Consumes: `Base.metadata`, `Settings`.
- Produces: `alembic upgrade head` creates all 14 tables on an empty PostgreSQL 17 database and is idempotent.
- Produces: `TEST_DATABASE_URL`-based pytest fixtures: `test_database_url`, `migrated_database`, `db_engine`, `session_factory`, `clean_tables` (autouse per test).
- Produces: `alembic check` succeeds, proving the migration matches the ORM metadata.

- [ ] **Step 1: Write the failing migration test**

```python
# tests/integration/test_migrations.py
import os
import subprocess
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    "publisher_groups", "news_sources", "source_feeds", "source_permissions",
    "source_items", "source_item_content", "events", "event_items", "event_claims",
    "claim_evidence", "pipeline_runs", "daily_reports", "daily_report_stories",
    "story_sources", "alembic_version",
}


def run_alembic(*args: str, database_url: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "DATABASE_URL": database_url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        check=False, capture_output=True, text=True, env=env,
    )


async def test_migration_creates_expected_schema(
    migrated_database: str, db_engine: AsyncEngine,
) -> None:
    async with db_engine.connect() as connection:
        rows = await connection.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))
        assert {row[0] for row in rows} == EXPECTED_TABLES

        index_names = await connection.execute(text(
            "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"
        ))
        names = {row[0] for row in index_names}
        assert "uq_current_published_report_per_day" in names
        assert "uq_source_items_external_id" in names


async def test_upgrade_is_idempotent_and_matches_models(migrated_database: str) -> None:
    again = run_alembic("upgrade", "head", database_url=migrated_database)
    assert again.returncode == 0, again.stderr
    check = run_alembic("check", database_url=migrated_database)
    assert check.returncode == 0, check.stdout + check.stderr
```

- [ ] **Step 2: Start a disposable PostgreSQL for the test suite**

Run (Docker daemon must be running):

```powershell
docker run -d --rm --name dst-test-db -e POSTGRES_USER=daily_signal -e POSTGRES_PASSWORD=daily_signal -e POSTGRES_DB=daily_signal_test -p 55432:5432 postgres:17-alpine
$env:TEST_DATABASE_URL = "postgresql+asyncpg://daily_signal:daily_signal@127.0.0.1:55432/daily_signal_test"
```

Expected: container starts; `docker exec dst-test-db pg_isready -U daily_signal` eventually reports ready.

- [ ] **Step 3: Write the failing fixtures and run the test**

`tests/conftest.py` must skip integration tests when `TEST_DATABASE_URL` is unset rather than fail. The session-scoped `migrated_database` fixture converts the SQLAlchemy URL to a plain asyncpg DSN by removing `+asyncpg`, connects with `asyncpg`, executes `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`, then runs `alembic upgrade head` in a subprocess with `DATABASE_URL` set to the original SQLAlchemy test URL. The `db_engine` fixture creates one async engine; `session_factory` wraps it. The autouse `clean_tables` fixture truncates every table except `alembic_version` before each test. Never read or destroy `DATABASE_URL`; only `TEST_DATABASE_URL` is touched.

Run: `uv run pytest tests/integration/test_migrations.py -v`
Expected: FAIL because `alembic.ini`/migration do not exist.

- [ ] **Step 4: Create Alembic and generate the migration**

Configure `alembic.ini` with `script_location = migrations`, `prepend_sys_path = src`, and a placeholder URL. `migrations/env.py` reads `DATABASE_URL`, uses `Base.metadata` as `target_metadata`, and supports async engines. Generate from the live test database:

```powershell
$env:DATABASE_URL = $env:TEST_DATABASE_URL
uv run alembic revision --autogenerate --rev-id 0001 -m "initial schema"
```

Inspect the generated `migrations/versions/0001_initial.py`: `revision = "0001"`, `down_revision = None`, all 14 tables, all named constraints/indexes, and PostgreSQL dialect types (`JSONB`, `postgresql_where`, `CHAR(2)`, `NUMERIC`). Fix autogenerate omissions by comparing against `schema.sql`; do not rely on the generated file unseen.

- [ ] **Step 5: Run the migration tests to verify they pass**

Run: `uv run pytest tests/integration/test_migrations.py -v`
Expected: PASS (both tests).

- [ ] **Step 6: Commit**

```powershell
git add alembic.ini migrations tests/conftest.py tests/integration
git commit -m "feat: add initial Alembic migration and database test harness"
```

---

### Task 5: Source seeding and CLI

**Files:**
- Create: `src/daily_signal/infrastructure/db/seed.py`
- Create: `src/daily_signal/cli.py`
- Create: `tests/unit/test_sources_config.py`, `tests/integration/test_seed.py`

**Interfaces:**
- Produces: `load_sources_config(path: Path) -> SourcesConfig`; `SourcesConfig.sources: tuple[SourceConfig, ...]`.
- Produces: `async def seed_sources(session: AsyncSession, config: SourcesConfig) -> SeedSummary`; `SeedSummary(created: int, skipped: int)`.
- Produces: `stable_uuid(kind: str, key: str) -> UUID` using UUIDv5 in `NAMESPACE_URL` with prefix `daily-signal`.
- Produces: CLI `python -m daily_signal.cli seed-sources [--config PATH]`; prints a JSON summary and exits 0.

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_sources_config.py
from pathlib import Path

import pytest

from daily_signal.infrastructure.db.seed import SourceConfigError, load_sources_config

ROOT = Path(__file__).resolve().parents[2]


def test_loads_three_in_review_sources() -> None:
    config = load_sources_config(ROOT / "config/sources.yaml")
    assert len(config.sources) == 3
    assert {source.slug for source in config.sources} == {
        "global-voices", "netzpolitik-org", "el-salto",
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
```

```python
# tests/integration/test_seed.py
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from daily_signal.infrastructure.db.models import (
    NewsSource, PublisherGroup, SourceFeed, SourcePermission,
)
from daily_signal.infrastructure.db.seed import load_sources_config, seed_sources

pytestmark = pytest.mark.integration


async def test_seed_is_idempotent_and_locks_rights(
    session_factory, clean_tables, migrated_database: str,
) -> None:
    config = load_sources_config("config/sources.yaml")
    async with session_factory() as session:
        first = await seed_sources(session, config)
        await session.commit()
        second = await seed_sources(session, config)
        await session.commit()
        assert first.created == 3
        assert second.created == 0

        assert await session.scalar(select(func.count()).select_from(NewsSource)) == 3
        assert await session.scalar(select(func.count()).select_from(PublisherGroup)) == 3
        assert await session.scalar(select(func.count()).select_from(SourceFeed)) == 3
        assert await session.scalar(select(func.count()).select_from(SourcePermission)) == 3

        sources = (await session.scalars(select(NewsSource))).all()
        assert all(source.review_status == "in_review" for source in sources)
        assert all(source.enabled is False for source in sources)
        permissions = (await session.scalars(select(SourcePermission))).all()
        assert all(permission.review_status == "in_review" for permission in permissions)
        assert all(permission.publish_derivatives is False for permission in permissions)
        assert all(permission.send_to_external_llm is False for permission in permissions)


async def test_seed_never_re_enables_or_downgrades_an_existing_source(
    session_factory, clean_tables, migrated_database: str,
) -> None:
    config = load_sources_config("config/sources.yaml")
    async with session_factory() as session:
        await seed_sources(session, config)
        await session.commit()
        source = await session.scalar(select(NewsSource).where(NewsSource.slug == "global-voices"))
        assert source is not None
        source.review_status = "approved"
        source.enabled = True
        await session.commit()

        await seed_sources(session, config)
        await session.commit()
        await session.refresh(source)
        assert source.review_status == "approved"
        assert source.enabled is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/test_sources_config.py tests/integration/test_seed.py -v`
Expected: FAIL with import errors.

- [ ] **Step 3: Implement seeding and CLI**

Define Pydantic models for the YAML keys (`version`, `sources`, `permission_defaults`). `load_sources_config` must raise `SourceConfigError` unless: version is `1`; every source has `review_status == "in_review"`, `enabled is False`, `permissions_approved is False`; and every permission default is `False` except `review_status == "in_review"`. This is a deliberate guard against config-driven rights escalation.

Seed each source and publisher group by slug, creating them only when absent. Create `SourceFeed` by `feed_url` and `SourcePermission` revision 1 with every flag `false`, `review_status="in_review"`, license/terms/scope/attribution copied from YAML. Use `stable_uuid("publisher-group", slug)`, `stable_uuid("source", slug)`, `stable_uuid("feed", slug)`, `stable_uuid("permission", slug)` so reruns are deterministic. Never update an existing source's `enabled`, `review_status`, or permission flags.

The CLI uses `argparse`: `seed-sources` opens an engine/session from `get_settings()`, runs the seed in one transaction, prints `{"created": N, "skipped": M}`, returns 0; on `SourceConfigError` prints the error to stderr and returns 2. `python -m daily_signal.cli` must work (add `if __name__ == "__main__": raise SystemExit(main())`).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/unit/test_sources_config.py tests/integration/test_seed.py -v`
Expected: PASS. Also run `uv run python -m daily_signal.cli seed-sources --config config/sources.yaml` against the test database and confirm the JSON summary.

- [ ] **Step 5: Commit**

```powershell
git add src/daily_signal/infrastructure/db/seed.py src/daily_signal/cli.py tests/unit/test_sources_config.py tests/integration/test_seed.py
git commit -m "feat: seed rights-locked news sources via CLI"
```

---

### Task 6: FastAPI application foundation, errors, request IDs, health

**Files:**
- Create: `src/daily_signal/main.py`
- Create: `src/daily_signal/api/__init__.py`, `api/dependencies.py`, `api/errors.py`, `api/middleware.py`
- Create: `src/daily_signal/api/schemas/__init__.py`, `api/schemas/base.py`, `api/schemas/errors.py`, `api/schemas/health.py`
- Create: `src/daily_signal/api/v1/__init__.py`, `api/v1/router.py`
- Create: `tests/integration/test_api_health.py`

**Interfaces:**
- Produces: `create_app(settings: Settings | None = None) -> FastAPI`; module-level `app = create_app()`.
- Produces: `app.state.settings`, `app.state.engine`, `app.state.session_factory`.
- Produces: `ApiErrorException(status_code: int, code: str, message: str)` and the standard envelope `{"error": {"code": str, "message": str, "requestId": str}}`.
- Produces: `get_session(request) -> AsyncIterator[AsyncSession]`, `get_settings(request) -> Settings`.
- Produces: `RequestIdMiddleware` (sets `request.state.request_id` from UUID4, returns `X-Request-ID`), `RateLimitMiddleware` (only `/v1/`, in-memory fixed window, configurable via `rate_limit_per_minute`, disabled at `0`).
- Produces: `ApiModel` Pydantic base with camelCase aliases.

- [ ] **Step 1: Write the failing health/error tests**

```python
# tests/integration/test_api_health.py
import pytest
from httpx import ASGITransport, AsyncClient
from asgi_lifespan import LifespanManager

from daily_signal.core.config import Settings
from daily_signal.main import create_app

pytestmark = pytest.mark.integration


async def test_live_returns_ok(client) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


async def test_ready_returns_ok_when_database_is_available(client) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_returns_503_when_database_is_unavailable(migrated_database: str) -> None:
    app = create_app(Settings(
        database_url="postgresql+asyncpg://nobody:nobody@127.0.0.1:1/nothing",
        rate_limit_per_minute=0,
    ))
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "service_unavailable"
    assert body["error"]["requestId"] == response.headers["X-Request-ID"]


async def test_unknown_route_uses_error_envelope(client) -> None:
    response = await client.get("/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]
    assert body["error"]["requestId"] == response.headers["X-Request-ID"]
```

Add an `app` fixture to `tests/conftest.py` that calls `create_app(Settings(database_url=test_database_url, rate_limit_per_minute=0))`. Add a `client` fixture that wraps `app` in `LifespanManager` and `AsyncClient`. Add `asgi-lifespan` to the dev dependencies if it is not already there.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/integration/test_api_health.py -v`
Expected: FAIL because `daily_signal.main` does not exist.

- [ ] **Step 3: Implement the application foundation**

`create_app` creates the engine/session factory, configures logging, registers lifespan disposal, and includes `api_router` (`APIRouter(prefix="/v1")`) plus the two health routes. If `settings.cors_origins` is non-empty, add `CORSMiddleware` with those origins, credentials disabled, and all methods/headers. Do not create tables at startup. Readiness runs `SELECT 1` through the session factory and raises `ApiErrorException(503, "service_unavailable", ...)` on failure.

`ApiModel` sets `alias_generator=to_camel` and `populate_by_name=True`. `ApiError` and `HealthStatus` match the contract exactly and use `additionalProperties: false` semantics via `model_config = ConfigDict(extra="forbid")`.

Register exception handlers for `ApiErrorException`, `RequestValidationError`, `StarletteHTTPException`, and unhandled `Exception`. Every handler returns the envelope; `RequestValidationError` maps to `422 invalid_parameter` without echoing raw input. Middleware order: add `RateLimitMiddleware` first, then `RequestIdMiddleware` so the ID exists before rate limiting. Rate-limit responses also use the envelope and include `Retry-After` (integer seconds, minimum 1).

`/v1/days` does not exist yet in this task; its `422 invalid_parameter` path is covered by the malformed-date test in Task 7. Do not invent test-only routes.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/integration/test_api_health.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/daily_signal/main.py src/daily_signal/api tests/integration/test_api_health.py tests/conftest.py
git commit -m "feat: add FastAPI foundation with errors, request IDs, and health checks"
```

---

### Task 7: Published report and story endpoints with ETags and rate limiting

**Files:**
- Create: `src/daily_signal/application/__init__.py`, `application/ports/__init__.py`, `application/ports/repositories.py`
- Create: `src/daily_signal/application/queries/__init__.py`, `application/queries/get_daily_report.py`, `application/queries/list_daily_reports.py`
- Create: `src/daily_signal/infrastructure/db/repositories/__init__.py`, `infrastructure/db/repositories/reports.py`
- Create: `src/daily_signal/api/etag.py`, `api/schemas/days.py`, `api/schemas/stories.py`, `api/schemas/mapping.py`
- Create: `src/daily_signal/api/v1/days.py`, `api/v1/stories.py`
- Create: `tests/contract/validation.py`, `tests/fixtures/factories.py`
- Create: `tests/integration/test_api_reports.py`

**Interfaces:**
- Produces: `ReportRecord`, `StorySourceRecord`, `StoryRecord`, `DailyReportRecord`, `DailyReportRepository` protocol exactly as listed below.
- Produces: `SqlAlchemyDailyReportRepository(session)` implementing the protocol.
- Produces: query functions `get_daily_report(repo, report_date)`, `get_latest_daily_report(repo)`, `list_daily_reports(repo, from_date, to_date)`, `get_story(repo, story_id)`.
- Produces: `make_report_etag(report_id: UUID, revision: int) -> str`, `etag_matches(if_none_match: str | None, etag: str) -> bool`, `make_days_etag(from_date, to_date, days) -> str`.
- Produces: DTOs `DayScore`, `DaySummary`, `DailyReport`, `DayCollection`, `StorySource`, `Story`, `StoryCollection` matching `contracts/openapi.yaml`.
- Produces: `assert_valid(instance: object, schema_name: str) -> None` in `tests/contract/validation.py`.

**Interfaces for the repository (later tasks rely on these exact names):**

```python
@dataclass(frozen=True)
class ReportRecord:
    id: UUID
    report_date: date
    revision: int
    headline: str
    summary: str
    score: int
    raw_score: Decimal
    score_label: DayLabel
    score_confidence: Confidence
    score_explanation: str
    methodology_version: str
    published_at: datetime
    story_count: int

@dataclass(frozen=True)
class StorySourceRecord:
    id: UUID
    source_id: UUID
    publisher: str
    url: str
    original_title: str | None
    author: str | None
    published_at: datetime
    updated_at: datetime | None
    language: str
    license_code: str | None
    license_url: str | None
    attribution: str | None
    originating_agency: str | None
    content_modified: bool
    modification_notice: str | None

@dataclass(frozen=True)
class StoryRecord:
    id: UUID
    rank: int
    title: str
    summary: str
    why_it_matters: str
    category: Category
    region: Region
    direction: Direction
    impact: int
    content_basis: ContentBasis
    derivative_license_code: str | None
    derivative_license_url: str | None
    modification_notice: str | None
    sources: tuple[StorySourceRecord, ...]

@dataclass(frozen=True)
class DailyReportRecord(ReportRecord):
    stories: tuple[StoryRecord, ...]

class DailyReportRepository(Protocol):
    async def get_current_by_date(self, report_date: date) -> DailyReportRecord | None: ...
    async def get_latest(self) -> DailyReportRecord | None: ...
    async def list_current(self, from_date: date, to_date: date) -> list[ReportRecord]: ...
    async def get_current_story(self, story_id: UUID) -> StoryRecord | None: ...
```

- [ ] **Step 1: Write the failing tests**

Create `tests/contract/validation.py` first (it is test infrastructure, not production code):

```python
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text(encoding="utf-8"))
RESOURCE = Resource.from_contents(CONTRACT, default_specification=DRAFT202012)
REGISTRY = Registry().with_resource("urn:daily-signal:contract", RESOURCE)


def assert_valid(instance: object, schema_name: str) -> None:
    schema = {"$ref": f"urn:daily-signal:contract#/components/schemas/{schema_name}"}
    errors = list(Draft202012Validator(schema, registry=REGISTRY).iter_errors(instance))
    assert not errors, [error.message for error in errors]
```

Add the `published_report` fixture to `tests/fixtures/factories.py`: one publisher group, one approved+enabled source with an approved permission (all needed rights true), one feed, five approved items, five events, one `daily_reports` row with `status="published"`, `is_current=True`, `revision=1`, `score=3`, `raw_score=0`, `score_label="mixed"`, `score_confidence="high"`, complete text fields, `published_at` UTC, five `daily_report_stories`, and one `story_sources` snapshot per story. Use these exact story rows so the fixture's score is consistent and the AND-filter test is non-empty:

| rank | direction | direction_value | impact | region |
|---|---|---|---|---|
| 1 | negative | -2 | 1 | germany |
| 2 | neutral | 0 | 2 | europe |
| 3 | positive | 2 | 1 | world |
| 4 | negative | -1 | 1 | europe |
| 5 | positive | 1 | 1 | germany |

The weighted mean is `(-2 + 0 + 2 - 1 + 1) / (1 + 4 + 1 + 1 + 1) = 0`, so `score=3`, `raw_score=0`. Also create a superseded revision 2 with `is_current=False` and a story that must remain invisible. The fixture returns IDs by name (`report_id`, `current_story_ids`, `superseded_story_id`).

Then write the integration tests:

```python
# tests/integration/test_api_reports.py
import pytest

from tests.contract.validation import assert_valid

pytestmark = pytest.mark.integration


async def test_empty_calendar_returns_exact_empty_body(client) -> None:
    response = await client.get("/v1/days", params={"from": "2026-11-01", "to": "2026-11-30"})
    assert response.status_code == 200
    assert response.json() == {"from": "2026-11-01", "to": "2026-11-30", "days": []}


async def test_latest_without_report_returns_404_envelope(client) -> None:
    response = await client.get("/v1/days/latest")
    assert response.status_code == 404
    assert_valid(response.json(), "ApiError")


async def test_invalid_ranges_return_400(client) -> None:
    response = await client.get("/v1/days", params={"from": "2026-11-30", "to": "2026-11-01"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_date_range"
    response = await client.get("/v1/days", params={"from": "2024-01-01", "to": "2025-12-31"})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "date_range_too_large"


async def test_malformed_date_returns_422(client) -> None:
    response = await client.get("/v1/days", params={"from": "not-a-date", "to": "2026-11-30"})
    assert response.status_code == 422
    assert_valid(response.json(), "ApiError")


async def test_latest_and_by_date_return_contract_valid_reports(
    client, published_report,
) -> None:
    latest = await client.get("/v1/days/latest")
    assert latest.status_code == 200
    assert_valid(latest.json(), "DailyReport")
    assert latest.json()["date"] == "2026-11-12"
    assert len(latest.json()["stories"]) == 5
    etag = latest.headers["ETag"]
    assert etag

    not_modified = await client.get("/v1/days/latest", headers={"If-None-Match": etag})
    assert not_modified.status_code == 304
    assert not not_modified.content

    by_date = await client.get("/v1/days/2026-11-12")
    assert by_date.status_code == 200
    assert_valid(by_date.json(), "DailyReport")
    assert by_date.headers["ETag"] == etag


async def test_calendar_lists_only_current_published_days(client, published_report) -> None:
    response = await client.get("/v1/days", params={"from": "2026-11-01", "to": "2026-11-30"})
    assert response.status_code == 200
    body = response.json()
    assert_valid(body, "DayCollection")
    assert [day["date"] for day in body["days"]] == ["2026-11-12"]
    assert body["days"][0]["storyCount"] == 5
    assert response.headers["ETag"]


async def test_story_filters_combine_with_and(client, published_report) -> None:
    response = await client.get(
        "/v1/days/2026-11-12/stories", params={"direction": "negative", "region": "germany"},
    )
    assert response.status_code == 200
    assert_valid(response.json(), "StoryCollection")
    assert len(response.json()["stories"]) == 1
    assert all(story["direction"] == "negative" for story in response.json()["stories"])
    assert all(story["region"] == "germany" for story in response.json()["stories"])
    invalid = await client.get("/v1/days/2026-11-12/stories", params={"direction": "sideways"})
    assert invalid.status_code == 422


async def test_superseded_revision_and_its_stories_are_invisible(
    client, published_report,
) -> None:
    response = await client.get(f"/v1/stories/{published_report['superseded_story_id']}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_current_story_returns_attribution_snapshot(client, published_report) -> None:
    story_id = published_report["current_story_ids"][0]
    response = await client.get(f"/v1/stories/{story_id}")
    assert response.status_code == 200
    assert_valid(response.json(), "Story")
    assert response.json()["sources"][0]["publisher"]
    assert response.json()["sources"][0]["attribution"]


async def test_rate_limit_returns_429_with_retry_after(
    published_report, test_database_url: str,
) -> None:
    from asgi_lifespan import LifespanManager
    from httpx import ASGITransport, AsyncClient

    from daily_signal.core.config import Settings
    from daily_signal.main import create_app

    app = create_app(Settings(
        database_url=test_database_url,
        rate_limit_per_minute=2,
    ))
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            assert (await client.get("/v1/days/2026-11-12")).status_code == 200
            assert (await client.get("/v1/days/2026-11-12")).status_code == 200
            limited = await client.get("/v1/days/2026-11-12")
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) >= 1
    assert_valid(limited.json(), "ApiError")
```

Add ETag tests for `If-None-Match` with multiple/weak values (`W/"<etag>"` must match) and a mismatching tag must return 200.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/integration/test_api_reports.py -v`
Expected: FAIL with missing modules/fixtures.

- [ ] **Step 3: Implement the repository, queries, DTOs, and routes**

Repository rules: every report query filters `status="published"` and `is_current=True`; `get_latest` orders by `report_date DESC, published_at DESC` and returns one; `list_current` orders by `report_date ASC`; `get_current_story` joins story to report and filters current/published. Load stories ordered by `rank`, then load all sources for those story IDs in one query and group them. `StorySource.id` is the `source_items.id`; `StorySource.source_id` is `source_items.source_id`; publisher/url/title/author/license/attribution/agency/modification come from the `story_sources` snapshot; timestamps/language come from `source_items`. Select `publisher_snapshot`, not the current publisher name.

Query functions are thin application services that validate the date range before calling the repository? No: range validation is API input validation and belongs in the route. Query functions only orchestrate repository calls and return records.

DTO mapping: `DaySummary.storyCount` is `record.story_count` (the repository sets it from a count query for list results and from `len(stories)` for single reports); `DayScore.max` is `5`; `DayScore.rawValue` is `float(raw_score)`; `DailyReport.timezone` is the literal `"Europe/Berlin"`; `DailyReport.methodologyVersion` comes from the record. All DTOs use `ApiModel`. `StoryCollection.date` is the requested date and `stories` is filtered in memory (max 8) with AND semantics. Do not expose `direction_value`.

Routes: register `/v1/days/latest` before `/v1/days/{date}`. `/v1/days` aliases `from`/`to` with `Query(alias=...)` and requires both. Use `response: Response` to set ETag headers. For conditional requests, compare `If-None-Match` against the computed ETag and return `Response(status_code=304, headers={"ETag": etag})` on a match. Return `404` via `ApiErrorException` for any missing/unpublished resource.

Rate limiting: fixed 60-second window keyed by client IP, only for paths starting `/v1/`, return `429` with code `rate_limited`, message, request ID, and `Retry-After`. Exempt `/health/*`.

- [ ] **Step 4: Run the report tests to verify they pass**

Run: `uv run pytest tests/integration/test_api_reports.py tests/integration/test_api_health.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/daily_signal/application src/daily_signal/infrastructure/db/repositories src/daily_signal/api tests/contract/validation.py tests/fixtures tests/integration/test_api_reports.py tests/integration/test_api_health.py
git commit -m "feat: serve published reports and stories with ETags"
```

---

### Task 8: Approved sources and methodology endpoints

**Files:**
- Create: `config/methodology.yaml`
- Create: `src/daily_signal/application/methodology.py`
- Create: `src/daily_signal/infrastructure/db/repositories/sources.py`
- Create: `src/daily_signal/api/schemas/sources.py`, `api/schemas/methodology.py`
- Create: `src/daily_signal/api/v1/sources.py`, `api/v1/methodology.py`
- Create: `tests/integration/test_api_sources.py`

**Interfaces:**
- Extends `application/ports/repositories.py` with `SourceRecord` and `SourceRepository`.
- Produces: `load_methodology(path: Path) -> MethodologyConfig`; `MethodologyConfig` validates four thresholds, the five exact colors, and a non-empty version/description.
- Produces: `SqlAlchemySourceRepository(session).list_approved() -> list[SourceRecord]`.
- Produces: `GET /v1/sources` and `GET /v1/methodology` matching the contract.

- [ ] **Step 1: Write the failing tests**

```python
# tests/integration/test_api_sources.py
from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from sqlalchemy import select

from daily_signal.infrastructure.db.models import NewsSource, SourcePermission
from tests.contract.validation import assert_valid

pytestmark = pytest.mark.integration


async def test_seed_sources_are_not_public(client, seeded_sources) -> None:
    response = await client.get("/v1/sources")
    assert response.status_code == 200
    assert response.json() == {"sources": []}


async def test_only_approved_enabled_sources_with_approved_permission_are_public(
    client, session_factory, seeded_sources,
) -> None:
    async with session_factory() as session:
        source = await session.scalar(select(NewsSource).where(NewsSource.slug == "global-voices"))
        assert source is not None
        source.review_status = "approved"
        source.enabled = True
        permission = await session.scalar(
            select(SourcePermission).where(SourcePermission.source_id == source.id)
        )
        assert permission is not None
        permission.review_status = "approved"
        permission.approved_by = "test"
        permission.approved_at = permission.created_at
        await session.commit()

    response = await client.get("/v1/sources")
    assert response.status_code == 200
    assert_valid(response.json(), "SourceCollection")
    assert [source["slug"] for source in response.json()["sources"]] == ["global-voices"]
    assert response.json()["sources"][0]["licenseCode"] == "CC-BY-3.0"


async def test_latest_permission_revision_must_be_approved(
    client, session_factory, seeded_sources,
) -> None:
    async with session_factory() as session:
        source = await session.scalar(select(NewsSource).where(NewsSource.slug == "global-voices"))
        assert source is not None
        source.review_status = "approved"
        source.enabled = True
        first = await session.scalar(
            select(SourcePermission).where(SourcePermission.source_id == source.id)
        )
        assert first is not None
        first.review_status = "approved"
        first.approved_by = "test"
        first.approved_at = first.created_at
        session.add(SourcePermission(
            id=uuid4(), source_id=source.id, revision=2, review_status="in_review",
            license_code=first.license_code, license_url=first.license_url,
            terms_url=first.terms_url, content_scope=first.content_scope,
            attribution_requirements=first.attribution_requirements,
        ))
        await session.commit()

    response = await client.get("/v1/sources")
    assert response.json() == {"sources": []}


async def test_methodology_returns_pinned_values(client) -> None:
    response = await client.get("/v1/methodology")
    assert response.status_code == 200
    assert_valid(response.json(), "Methodology")
    assert response.json()["timezone"] == "Europe/Berlin"
    assert response.json()["scoreScale"] == 5
    assert response.json()["scoreThresholds"] == [-1.1, -0.3, 0.3, 1.1]
    assert response.json()["scoreColors"] == {
        "very_negative": "#CF6666", "negative": "#DE9A57", "mixed": "#B8AC69",
        "positive": "#85B78A", "very_positive": "#43A779",
    }


async def test_generated_openapi_matches_contract_route_inventory(app) -> None:
    contract = yaml.safe_load(Path("contracts/openapi.yaml").read_text(encoding="utf-8"))
    generated = app.openapi()
    contract_routes = {
        (path, method)
        for path, item in contract["paths"].items()
        for method in item
    }
    generated_routes = {
        (path, method)
        for path, item in generated["paths"].items()
        if path.startswith(("/v1", "/health"))
        for method in item
    }
    assert generated_routes == contract_routes
    for path, method in contract_routes:
        assert (
            generated["paths"][path][method]["operationId"]
            == contract["paths"][path][method]["operationId"]
        )
```

Add `seeded_sources` to `tests/conftest.py`: run `load_sources_config` + `seed_sources` in a session before the test, after `clean_tables`. Import `uuid4` in the test.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/integration/test_api_sources.py -v`
Expected: FAIL because the endpoints do not exist.

- [ ] **Step 3: Implement the methodology config and source repository**

`config/methodology.yaml` (exact values; keep the description factual):

```yaml
version: "1.0.0"
timezone: Europe/Berlin
score_scale: 5
relevance_weights:
  impact: 100
score_thresholds: [-1.1, -0.3, 0.3, 1.1]
score_colors:
  very_negative: "#CF6666"
  negative: "#DE9A57"
  mixed: "#B8AC69"
  positive: "#85B78A"
  very_positive: "#43A779"
description: >-
  Weighted day score from story direction and squared impact. Mixed and unknown
  stories are excluded. Only current published reports with high or medium
  confidence are served.
```

`load_methodology` uses Pydantic with `extra="forbid"`, validates `len(score_thresholds) == 4` and colors matching `^#[0-9A-Fa-f]{6}$`, and is loaded once in the app lifespan into `app.state.methodology`. The route serializes it with camelCase aliases.

Source query: select enabled sources with `review_status="approved"`, join their latest permission revision (`DISTINCT ON (source_id) ... ORDER BY source_id, revision DESC`), and include only rows where that latest revision is approved. Return `SourceRecord` with `website=homepage_url`, `role=source_type`, and `license_code` from that permission. Order by `slug`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/integration/test_api_sources.py tests/integration/test_api_reports.py tests/integration/test_api_health.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add config/methodology.yaml src/daily_signal/application/methodology.py src/daily_signal/infrastructure/db/repositories/sources.py src/daily_signal/api/schemas/sources.py src/daily_signal/api/schemas/methodology.py src/daily_signal/api/v1/sources.py src/daily_signal/api/v1/methodology.py tests/integration/test_api_sources.py tests/conftest.py
git commit -m "feat: expose approved sources and methodology"
```

---

### Task 9: Worker, scheduler, advisory lock, Docker Compose

**Files:**
- Create: `src/daily_signal/jobs/__init__.py`, `jobs/worker.py`, `jobs/scheduler.py`
- Create: `src/daily_signal/infrastructure/db/locks.py`
- Modify: `src/daily_signal/cli.py` (add `worker` and `scheduler` commands)
- Create: `Dockerfile`, `compose.yaml`, `compose.dev.yaml`, `docker/initdb/01-test-database.sql`
- Create: `tests/unit/test_scheduler.py`, `tests/integration/test_advisory_lock.py`

**Interfaces:**
- Produces: `async def run_worker(settings: Settings, stop_event: asyncio.Event) -> None`; logs a heartbeat every 5 seconds, survives transient DB errors, exits cleanly on stop.
- Produces: `async def run_scheduler(settings: Settings, stop_event: asyncio.Event) -> None`; sleeps `settings.scheduler_tick_seconds`, calls `tick()`, and exits cleanly on stop.
- Produces: `next_target_date(now: datetime) -> date` (previous Europe/Berlin day) and `async def tick(session_factory, now: datetime) -> bool`; returns `True` when the daily analysis is due and the advisory lock was acquired, `False` otherwise. It logs `daily_analysis_due` with the target date but does not create fake reports.
- Produces: `async def try_advisory_lock(session: AsyncSession, key: int) -> bool`, `async def release_advisory_lock(session: AsyncSession, key: int) -> None`.
- Produces: Compose services `db`, `migrate`, `api`, `worker`, `scheduler`; `migrate` runs `alembic upgrade head` and `seed-sources` once; api/worker/scheduler wait for it.

- [ ] **Step 1: Write the failing scheduler and lock tests**

```python
# tests/unit/test_scheduler.py
from datetime import datetime
from zoneinfo import ZoneInfo

from daily_signal.jobs.scheduler import next_target_date

BERLIN = ZoneInfo("Europe/Berlin")


def test_target_date_is_the_previous_berlin_day() -> None:
    assert next_target_date(datetime(2026, 11, 13, 3, 30, tzinfo=BERLIN)).isoformat() == "2026-11-12"


def test_target_date_rolls_over_at_midnight() -> None:
    assert next_target_date(datetime(2026, 1, 1, 0, 5, tzinfo=BERLIN)).isoformat() == "2025-12-31"
```

```python
# tests/integration/test_advisory_lock.py
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from daily_signal.infrastructure.db.locks import release_advisory_lock, try_advisory_lock

pytestmark = pytest.mark.integration


async def test_advisory_lock_is_exclusive(
    session_factory: async_sessionmaker, clean_tables, migrated_database: str,
) -> None:
    async with session_factory() as first, session_factory() as second:
        assert await try_advisory_lock(first, 728191) is True
        assert await try_advisory_lock(second, 728191) is False
        await release_advisory_lock(first, 728191)
        assert await try_advisory_lock(second, 728191) is True
        await release_advisory_lock(second, 728191)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/unit/test_scheduler.py tests/integration/test_advisory_lock.py -v`
Expected: FAIL with import errors.

- [ ] **Step 3: Implement the processes and Compose runtime**

`try_advisory_lock` executes `SELECT pg_try_advisory_lock(:key)`; release executes `SELECT pg_advisory_unlock(:key)`. `tick` computes the target date as the previous Europe/Berlin day, returns `False` before 03:30 Berlin, and otherwise acquires the lock, logs `daily_analysis_due`, releases it, and returns `True`. It must not insert `pipeline_runs` while the workflow is unimplemented.

Worker loop: log `worker_heartbeat` every 5 seconds; catch `Exception`, log `worker_error` with only the exception class/message (no article text), sleep, continue. Scheduler loop: call `tick` every `scheduler_tick_seconds`; catch and log errors similarly. Both accept an `asyncio.Event` and return promptly when set. CLI `worker`/`scheduler` create the engine, install SIGINT/SIGTERM handlers (with a Windows fallback), run until signalled, then dispose.

`Dockerfile`: multi-stage or single `python:3.13-slim` image; install uv from `ghcr.io/astral-sh/uv:0.13.8`; copy `pyproject.toml`/`uv.lock`, run `uv sync --locked --no-dev --no-install-project`, copy `src`, `migrations`, `alembic.ini`, `config`, `contracts`, then `uv sync --locked --no-dev`; set `PATH=/app/.venv/bin:$PATH`; run as a non-root user; default command `uvicorn daily_signal.main:app --host 0.0.0.0 --port 8000`.

`compose.yaml`: `db` uses `postgres:17-alpine`, a named volume, `pg_isready` healthcheck, and no host port. `migrate` builds the image, waits for `db` healthy, runs `sh -c "alembic upgrade head && python -m daily_signal.cli seed-sources"`, and never restarts. `api` publishes `8000:8000`, depends on `migrate` with `condition: service_completed_successfully`, and has a Python-urllib healthcheck on `/health/live`. `worker` and `scheduler` use the same image and dependency, with `restart: unless-stopped`. `compose.dev.yaml` exposes `5432` for the db and mounts `./src`, `./config`, `./contracts` into the API/worker/scheduler; the API command adds `--reload` and `PYTHONPATH=/app/src`. `docker/initdb/01-test-database.sql` creates `daily_signal_test`.

- [ ] **Step 4: Verify the containers end to end**

Run:

```powershell
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod "http://localhost:8000/v1/days?from=2026-11-01&to=2026-11-30"
docker compose exec db psql -U daily_signal -d daily_signal -c "select slug, review_status, enabled from news_sources order by slug;"
docker compose logs --tail=50 worker scheduler
```

Expected: migrate exits 0; api/worker/scheduler run without restart loops; health checks return `{"status":"ok"}`; days returns `{"from":"2026-11-01","to":"2026-11-30","days":[]}`; all three sources are `in_review`/`f`; worker/scheduler logs show no traceback. Then run `docker compose down -v`.

- [ ] **Step 5: Run the automated tests**

Run: `uv run pytest tests/unit/test_scheduler.py tests/integration/test_advisory_lock.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/daily_signal/jobs src/daily_signal/infrastructure/db/locks.py src/daily_signal/cli.py Dockerfile compose.yaml compose.dev.yaml docker tests/unit/test_scheduler.py tests/integration/test_advisory_lock.py
git commit -m "feat: add worker, scheduler, and Docker Compose runtime"
```

---

### Task 10: CI workflows

**Files:**
- Create: `.github/workflows/ci.yml`, `.github/workflows/container.yml`
- Create: `tests/unit/test_ci_workflows.py`

**Interfaces:**
- Produces: CI on push/PR running `ruff check`, `ruff format --check`, `mypy src`, and `pytest` against PostgreSQL 17 with `TEST_DATABASE_URL` and `DATABASE_URL` set.
- Produces: container workflow building the Docker image without pushing.

- [ ] **Step 1: Write the failing workflow test**

```python
# tests/unit/test_ci_workflows.py
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/unit/test_ci_workflows.py -v`
Expected: FAIL with file-not-found.

- [ ] **Step 3: Create the workflows**

`ci.yml`: trigger on `push` and `pull_request`; one `test` job on `ubuntu-latest`; PostgreSQL 17 service with `POSTGRES_USER=daily_signal`, `POSTGRES_PASSWORD=daily_signal`, `POSTGRES_DB=daily_signal_test`, port 5432, and a `pg_isready` health option. Steps: checkout; `astral-sh/setup-uv@v6` with caching; `uv sync --locked`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src`; `uv run pytest -v`. Set both `DATABASE_URL` and `TEST_DATABASE_URL` to `postgresql+asyncpg://daily_signal:daily_signal@localhost:5432/daily_signal_test`.

`container.yml`: trigger on `push` and `pull_request`; buildx setup; `docker/build-push-action@v6` with `push: false`, `load: false`, tag `daily-signal:${{ github.sha }}`, and GitHub Actions cache. Do not reference secrets.

- [ ] **Step 4: Verify locally**

Run: `uv run pytest tests/unit/test_ci_workflows.py -v` and `uv run pytest tests/unit -v`.
Expected: PASS. Also run the CI command sequence locally against the test database and confirm it exits 0.

- [ ] **Step 5: Commit**

```powershell
git add .github/workflows tests/unit/test_ci_workflows.py
git commit -m "ci: add test and container build workflows"
```

---

### Task 11: Documentation, examples, and project README

**Files:**
- Modify: `README.md`
- Create: `docs/architecture.md`, `docs/data-model.md`, `docs/source-policy.md`, `docs/scoring-methodology.md`, `docs/adr/0001-modular-monolith.md`
- Create: `contracts/examples/daily-report.json`
- Create: `tests/contract/test_examples.py`

**Interfaces:**
- Produces: a German project README with purpose, status, quickstart, endpoints, test commands, source-rights warning, and explicit non-goals.
- Produces: docs that match the implemented behavior and the spec package; no claims of implemented feed adapters, LLM calls, or publishing workflow.
- Produces: contract-valid example payloads.

- [ ] **Step 1: Write the failing example test**

```python
# tests/contract/test_examples.py
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/contract/test_examples.py -v`
Expected: FAIL with file-not-found for `daily-report.json`.

- [ ] **Step 3: Write the README and docs**

README (German): describe Daily Signal as a read-only daily news report API; status = foundation, ingestion/LLM/publishing not implemented; quickstart with `uv sync --locked`, `docker compose up -d --build`, health/calendar/latest checks; endpoint table from the contract; test commands; source-rights section stating all three sources are `in_review` and disabled; repository map; explicit non-goals and next steps. Link to the docs and the spec package.

`docs/architecture.md`: modular monolith, dependency rule (api → application → domain; infrastructure implements ports), process separation, no admin API, migrations as a controlled step, ETag/revision semantics.

`docs/data-model.md`: 14 tables grouped by responsibility, relationships, revision model, rights-profile versioning, attribution snapshots, expiry of `source_item_content`, and the invariants enforced by the publication transaction rather than SQL (5–8 stories, supported claims, verified rights, source independence, threshold consistency, current-revision switch).

`docs/source-policy.md`: the three sources and their licenses/feeds; all initially `in_review`, disabled, all flags false; approval is a separate audited action; no automatic rights from CC/RSS; per-item verification; no raw text in logs; no browser-search pipeline.

`docs/scoring-methodology.md`: formula, thresholds, colors, impact-squared weighting, exclusion of mixed/unknown, confidence rules, and the publication threshold.

`docs/adr/0001-modular-monolith.md`: context, decision (one package/image, three processes), alternatives (separate services/repos, queue-first), consequences.

`contracts/examples/api-error.json`:

```json
{
  "error": {
    "code": "not_found",
    "message": "No published report for this date.",
    "requestId": "018f3c9e-7b2a-7c3d-9a10-6f4b2c1d8e90"
  }
}
```

`contracts/examples/daily-report.json`: a complete `DailyReport` with 5 stories, one source each, all required nullable fields present (including `null`), `timezone: "Europe/Berlin"`, `score.max: 5`, and valid enum values. It must pass the contract test.

- [ ] **Step 4: Run the example tests and full suite**

Run: `uv run pytest tests/contract/test_examples.py -v` then the full suite with the test database.
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add README.md docs contracts/examples tests/contract/test_examples.py
git commit -m "docs: document foundation, data model, and source policy"
```

---

## Final Verification Checklist

Run from the worktree with the test database available:

```powershell
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -v
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
Invoke-RestMethod "http://localhost:8000/v1/days?from=2026-11-01&to=2026-11-30"
docker compose exec db psql -U daily_signal -d daily_signal -c "select slug, review_status, enabled from news_sources order by slug;"
docker compose down -v
```

Definition of Done (from the spec):
- `uv sync --locked` works.
- `docker compose up -d --build` starts API and PostgreSQL; worker/scheduler run without crash loops.
- `alembic upgrade head` succeeds on an empty database and is idempotent.
- `/health/live` and `/health/ready` return `200` when healthy.
- Empty calendar returns exactly `{"from":"2026-11-01","to":"2026-11-30","days":[]}`.
- `/v1/days/latest` returns `404` in the standard error envelope when no report exists.
- All three sources are registered, `in_review`, disabled, with all productive permission flags false.
- CI runs linting, type checking, tests, migration check, and API contract checks.

## Explicit Non-Goals for This Plan

Feed adapters, HTTP ingestion, event clustering, LLM provider integration, prompt execution, report generation, validation workflow, publication/correction workflow, content purge jobs, authentication, admin UI, Caddy/TLS termination, and production deployment pipelines. These come after the foundation and are described in the spec package as next steps.
