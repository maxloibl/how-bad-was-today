"""Unit tests for the ETag helpers (no database required)."""

from uuid import UUID

from daily_signal.api.etag import etag_matches, make_report_etag

REPORT_ID = UUID("11111111-1111-1111-1111-111111111111")


def test_make_report_etag_is_quoted_id_and_revision() -> None:
    assert make_report_etag(REPORT_ID, 3) == f'"{REPORT_ID}:3"'


def test_etag_matches_requires_a_value() -> None:
    assert etag_matches(None, '"a:1"') is False
    assert etag_matches("", '"a:1"') is False


def test_etag_matches_exact_and_mismatched_tags() -> None:
    assert etag_matches('"a:1"', '"a:1"') is True
    assert etag_matches('"a:2"', '"a:1"') is False


def test_etag_matches_weak_tags() -> None:
    assert etag_matches('W/"a:1"', '"a:1"') is True


def test_etag_matches_multiple_tags_and_wildcard() -> None:
    assert etag_matches('"other", "a:1"', '"a:1"') is True
    assert etag_matches('"other", W/"a:1"', '"a:1"') is True
    assert etag_matches("*", '"a:1"') is True
    assert etag_matches('"other", "another"', '"a:1"') is False
