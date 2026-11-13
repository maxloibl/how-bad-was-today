from daily_signal.infrastructure.db import models  # noqa: F401  (registers models)
from daily_signal.infrastructure.db.base import Base

# (column, nullable) in schema-declaration order for every table.
EXPECTED_COLUMNS: dict[str, list[tuple[str, bool]]] = {
    "publisher_groups": [
        ("id", False),
        ("slug", False),
        ("name", False),
        ("country_code", False),
    ],
    "news_sources": [
        ("id", False),
        ("publisher_group_id", False),
        ("slug", False),
        ("name", False),
        ("homepage_url", False),
        ("source_type", False),
        ("origin_country", False),
        ("primary_language", False),
        ("review_status", False),
        ("enabled", False),
        ("reviewed_at", True),
        ("next_review_at", True),
        ("created_at", False),
        ("updated_at", False),
    ],
    "source_feeds": [
        ("id", False),
        ("source_id", False),
        ("feed_url", False),
        ("feed_kind", False),
        ("enabled", False),
        ("poll_interval_minutes", False),
        ("etag", True),
        ("http_last_modified", True),
        ("last_checked_at", True),
        ("last_success_at", True),
        ("consecutive_errors", False),
        ("created_at", False),
    ],
    "source_permissions": [
        ("id", False),
        ("source_id", False),
        ("revision", False),
        ("review_status", False),
        ("license_code", False),
        ("license_url", False),
        ("terms_url", False),
        ("evidence_url", True),
        ("content_scope", False),
        ("attribution_requirements", False),
        ("retention_hours", True),
        ("fetch_metadata", False),
        ("fetch_full_text", False),
        ("analyze_content", False),
        ("store_temporary", False),
        ("store_long_term", False),
        ("send_to_external_llm", False),
        ("create_embeddings", False),
        ("create_adaptations", False),
        ("republish_original_content", False),
        ("publish_derivatives", False),
        ("republish_media", False),
        ("approved_by", True),
        ("approved_at", True),
        ("created_at", False),
    ],
    "source_items": [
        ("id", False),
        ("source_id", False),
        ("feed_id", False),
        ("permission_id", False),
        ("external_id", True),
        ("original_url", False),
        ("canonical_url", False),
        ("original_title", False),
        ("author", True),
        ("language", False),
        ("published_at", False),
        ("updated_at", True),
        ("first_seen_at", False),
        ("last_seen_at", False),
        ("content_checksum", True),
        ("license_code", True),
        ("license_url", True),
        ("license_verified", False),
        ("contains_third_party_material", False),
        ("originating_agency", True),
        ("origin_group_key", True),
        ("editorial_type", False),
        ("ingestion_status", False),
    ],
    "source_item_content": [
        ("item_id", False),
        ("body_text", False),
        ("expires_at", False),
        ("stored_at", False),
    ],
    "events": [
        ("id", False),
        ("internal_title", False),
        ("event_date", True),
        ("event_time_estimate", True),
        ("region", False),
        ("category", False),
        ("first_seen_at", False),
        ("updated_at", False),
    ],
    "event_items": [
        ("event_id", False),
        ("item_id", False),
    ],
    "event_claims": [
        ("id", False),
        ("event_id", False),
        ("claim_text", False),
        ("verification_status", False),
        ("created_at", False),
    ],
    "claim_evidence": [
        ("claim_id", False),
        ("item_id", False),
        ("evidence_role", False),
    ],
    "pipeline_runs": [
        ("id", False),
        ("job_type", False),
        ("target_date", True),
        ("status", False),
        ("started_at", False),
        ("finished_at", True),
        ("model_provider", True),
        ("model_id", True),
        ("pipeline_version", False),
        ("prompt_version", True),
        ("methodology_version", True),
        ("input_tokens", True),
        ("output_tokens", True),
        ("estimated_cost_usd", True),
        ("error_code", True),
        ("quality_checks", False),
    ],
    "daily_reports": [
        ("id", False),
        ("report_date", False),
        ("revision", False),
        ("status", False),
        ("is_current", False),
        ("headline", True),
        ("summary", True),
        ("score", True),
        ("raw_score", True),
        ("score_label", True),
        ("score_confidence", True),
        ("score_explanation", True),
        ("methodology_version", False),
        ("prompt_version", False),
        ("pipeline_run_id", True),
        ("published_at", True),
        ("created_at", False),
    ],
    "daily_report_stories": [
        ("id", False),
        ("report_id", False),
        ("event_id", False),
        ("rank", False),
        ("title", False),
        ("summary", False),
        ("why_it_matters", False),
        ("category", False),
        ("region", False),
        ("direction", False),
        ("direction_value", True),
        ("impact", False),
        ("content_basis", False),
        ("derivative_license_code", True),
        ("derivative_license_url", True),
        ("modification_notice", True),
    ],
    "story_sources": [
        ("story_id", False),
        ("item_id", False),
        ("publisher_snapshot", False),
        ("url_snapshot", False),
        ("title_snapshot", True),
        ("author_snapshot", True),
        ("license_code_snapshot", True),
        ("license_url_snapshot", True),
        ("attribution_snapshot", True),
        ("origin_agency_snapshot", True),
        ("evidence_role", False),
        ("content_modified", False),
        ("modification_notice", True),
    ],
}

EXPECTED_TABLES = set(EXPECTED_COLUMNS)

# table -> set of (local_column, "referred_table.referred_column")
EXPECTED_FOREIGN_KEYS: dict[str, set[tuple[str, str]]] = {
    "news_sources": {("publisher_group_id", "publisher_groups.id")},
    "source_feeds": {("source_id", "news_sources.id")},
    "source_permissions": {("source_id", "news_sources.id")},
    "source_items": {
        ("source_id", "news_sources.id"),
        ("feed_id", "source_feeds.id"),
        ("permission_id", "source_permissions.id"),
        ("source_id", "source_feeds.source_id"),
        ("source_id", "source_permissions.source_id"),
    },
    "source_item_content": {("item_id", "source_items.id")},
    "event_items": {
        ("event_id", "events.id"),
        ("item_id", "source_items.id"),
    },
    "event_claims": {("event_id", "events.id")},
    "claim_evidence": {
        ("claim_id", "event_claims.id"),
        ("item_id", "source_items.id"),
    },
    "pipeline_runs": set(),
    "daily_reports": {("pipeline_run_id", "pipeline_runs.id")},
    "daily_report_stories": {
        ("report_id", "daily_reports.id"),
        ("event_id", "events.id"),
    },
    "story_sources": {
        ("story_id", "daily_report_stories.id"),
        ("item_id", "source_items.id"),
    },
}

EXPECTED_CHECK_NAMES: dict[str, set[str]] = {
    "news_sources": {
        "news_sources_source_type_check",
        "news_sources_review_status_check",
        "source_enable_requires_approval",
    },
    "source_feeds": {
        "source_feeds_feed_kind_check",
        "source_feeds_poll_interval_minutes_check",
        "source_feeds_consecutive_errors_check",
    },
    "source_permissions": {
        "source_permissions_revision_check",
        "source_permissions_review_status_check",
        "source_permissions_retention_hours_check",
        "permission_approval_has_auditor",
    },
    "source_items": {
        "source_items_editorial_type_check",
        "source_items_ingestion_status_check",
    },
    "events": {"events_region_check", "events_category_check"},
    "event_claims": {"event_claims_verification_status_check"},
    "claim_evidence": {"claim_evidence_evidence_role_check"},
    "pipeline_runs": {
        "pipeline_runs_job_type_check",
        "pipeline_runs_status_check",
        "pipeline_runs_input_tokens_check",
        "pipeline_runs_output_tokens_check",
        "pipeline_runs_estimated_cost_usd_check",
        "pipeline_finished_if_terminated",
    },
    "daily_reports": {
        "daily_reports_revision_check",
        "daily_reports_status_check",
        "daily_reports_score_check",
        "daily_reports_raw_score_check",
        "daily_reports_score_label_check",
        "daily_reports_score_confidence_check",
        "published_report_complete",
        "current_report_is_published",
    },
    "daily_report_stories": {
        "daily_report_stories_rank_check",
        "daily_report_stories_category_check",
        "daily_report_stories_region_check",
        "daily_report_stories_direction_check",
        "daily_report_stories_direction_value_check",
        "daily_report_stories_impact_check",
        "daily_report_stories_content_basis_check",
        "direction_consistent",
        "adaptation_metadata_required",
    },
    "story_sources": {"story_sources_evidence_role_check"},
}

EXPECTED_UNIQUE_NAMES: dict[str, set[str]] = {
    "publisher_groups": {"uq_publisher_groups_slug"},
    "news_sources": {"uq_news_sources_slug"},
    "source_feeds": {"uq_source_feeds_feed_url", "uq_source_feeds_id_source_id"},
    "source_permissions": {
        "uq_source_permissions_source_id_revision",
        "uq_source_permissions_id_source_id",
    },
    "source_items": {
        "uq_source_items_source_id_canonical_url",
        "uq_source_items_id_source_id",
    },
    "daily_reports": {"uq_daily_reports_report_date_revision"},
    "daily_report_stories": {
        "uq_daily_report_stories_report_id_event_id",
        "uq_daily_report_stories_report_id_rank",
    },
}

EXPECTED_INDEX_NAMES: dict[str, set[str]] = {
    "source_items": {
        "uq_source_items_external_id",
        "ix_source_items_time",
        "ix_source_items_source_time",
        "ix_source_items_status",
    },
    "source_item_content": {"ix_source_item_content_expiry"},
    "event_items": {"ix_event_items_item"},
    "claim_evidence": {"ix_claim_evidence_item"},
    "pipeline_runs": {"ix_pipeline_runs_target"},
    "daily_reports": {"uq_current_published_report_per_day", "ix_daily_reports_calendar"},
    "daily_report_stories": {"ix_daily_report_stories_report"},
    "story_sources": {"ix_story_sources_item"},
}


def _named(items: object) -> set[str]:
    return {item.name for item in items}  # type: ignore[attr-defined,arg-type]


def test_all_tables_are_declared() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_exact_columns_and_nullability() -> None:
    for table_name, expected in EXPECTED_COLUMNS.items():
        table = Base.metadata.tables[table_name]
        actual = [(c.name, bool(c.nullable)) for c in table.columns]
        assert actual == expected, f"{table_name}: column/nullable mismatch"


def test_foreign_key_targets() -> None:
    for table_name, expected in EXPECTED_FOREIGN_KEYS.items():
        table = Base.metadata.tables[table_name]
        actual = {
            (fk.parent.name, f"{fk.column.table.name}.{fk.column.name}")
            for fk in table.foreign_keys
        }
        assert actual == expected, f"{table_name}: foreign key mismatch"


def test_foreign_key_constraint_shapes() -> None:
    from sqlalchemy import ForeignKeyConstraint

    table = Base.metadata.tables["source_items"]
    actual = {
        (
            tuple(c.column_keys),
            tuple((e.column.table.name, e.column.name) for e in c.elements),
        )
        for c in table.constraints
        if isinstance(c, ForeignKeyConstraint)
    }
    assert actual == {
        (("feed_id",), (("source_feeds", "id"),)),
        (("source_id",), (("news_sources", "id"),)),
        (
            ("feed_id", "source_id"),
            (("source_feeds", "id"), ("source_feeds", "source_id")),
        ),
        (
            ("permission_id", "source_id"),
            (("source_permissions", "id"), ("source_permissions", "source_id")),
        ),
    }


def test_named_check_constraints() -> None:
    from sqlalchemy import CheckConstraint

    for table_name, expected in EXPECTED_CHECK_NAMES.items():
        table = Base.metadata.tables[table_name]
        actual = {c.name for c in table.constraints if isinstance(c, CheckConstraint)}
        assert actual == expected, f"{table_name}: CHECK constraint mismatch"


def test_named_unique_constraints() -> None:
    from sqlalchemy import UniqueConstraint

    for table_name, expected in EXPECTED_UNIQUE_NAMES.items():
        table = Base.metadata.tables[table_name]
        actual = {c.name for c in table.constraints if isinstance(c, UniqueConstraint)}
        assert actual == expected, f"{table_name}: UNIQUE constraint mismatch"


def test_index_names() -> None:
    for table_name, expected in EXPECTED_INDEX_NAMES.items():
        table = Base.metadata.tables[table_name]
        assert _named(table.indexes) == expected, f"{table_name}: index mismatch"


def test_index_expressions() -> None:
    items = Base.metadata.tables["source_items"]
    source_time = next(i for i in items.indexes if i.name == "ix_source_items_source_time")
    assert [str(e) for e in source_time.expressions] == [
        "source_items.source_id",
        "published_at DESC",
    ]
    assert source_time.dialect_options["postgresql"].get("where") is None

    runs = Base.metadata.tables["pipeline_runs"]
    target = next(i for i in runs.indexes if i.name == "ix_pipeline_runs_target")
    assert [str(e) for e in target.expressions] == [
        "pipeline_runs.target_date",
        "started_at DESC",
    ]
    assert target.dialect_options["postgresql"].get("where") is None


def test_foreign_key_constraint_names_are_unique_per_table() -> None:
    from sqlalchemy.dialects import postgresql
    from sqlalchemy.schema import CreateTable

    table = Base.metadata.tables["source_items"]
    ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
    fk_names = [c.name for c in table.constraints if c.__class__.__name__ == "ForeignKeyConstraint"]
    assert len(fk_names) == len(set(fk_names)), f"duplicate FK names: {fk_names}"
    assert "FOREIGN KEY(feed_id) REFERENCES source_feeds (id)" in ddl
    assert "FOREIGN KEY(feed_id, source_id) REFERENCES source_feeds (id, source_id)" in ddl


def test_critical_partial_index_predicates() -> None:
    items = Base.metadata.tables["source_items"]
    uq_ext = next(i for i in items.indexes if i.name == "uq_source_items_external_id")
    assert uq_ext.unique is True
    assert str(uq_ext.dialect_options["postgresql"]["where"]) == "external_id IS NOT NULL"

    reports = Base.metadata.tables["daily_reports"]
    uq_cur = next(i for i in reports.indexes if i.name == "uq_current_published_report_per_day")
    assert uq_cur.unique is True
    assert (
        str(uq_cur.dialect_options["postgresql"]["where"]) == "is_current AND status = 'published'"
    )
    ix_cal = next(i for i in reports.indexes if i.name == "ix_daily_reports_calendar")
    assert ix_cal.unique is False
    assert (
        str(ix_cal.dialect_options["postgresql"]["where"]) == "is_current AND status = 'published'"
    )
