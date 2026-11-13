import os
import subprocess
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration

EXPECTED_TABLES = {
    "publisher_groups",
    "news_sources",
    "source_feeds",
    "source_permissions",
    "source_items",
    "source_item_content",
    "events",
    "event_items",
    "event_claims",
    "claim_evidence",
    "pipeline_runs",
    "daily_reports",
    "daily_report_stories",
    "story_sources",
    "alembic_version",
}


def run_alembic(*args: str, database_url: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "DATABASE_URL": database_url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


async def test_migration_creates_expected_schema(
    migrated_database: str,
    db_engine: AsyncEngine,
) -> None:
    async with db_engine.connect() as connection:
        rows = await connection.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        assert {row[0] for row in rows} == EXPECTED_TABLES

        index_names = await connection.execute(
            text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
        )
        names = {row[0] for row in index_names}
        assert "uq_current_published_report_per_day" in names
        assert "uq_source_items_external_id" in names


async def test_upgrade_is_idempotent_and_matches_models(migrated_database: str) -> None:
    again = run_alembic("upgrade", "head", database_url=migrated_database)
    assert again.returncode == 0, again.stderr
    check = run_alembic("check", database_url=migrated_database)
    assert check.returncode == 0, check.stdout + check.stderr
