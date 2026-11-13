from daily_signal.infrastructure.db import models  # noqa: F401  (registers models)
from daily_signal.infrastructure.db.base import Base

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
