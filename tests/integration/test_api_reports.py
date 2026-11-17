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
    client,
    published_report,
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

    detail = await client.get("/v1/days/2026-11-12")
    assert detail.status_code == 200
    assert body["days"][0]["storyCount"] == len(detail.json()["stories"])

    not_modified = await client.get(
        "/v1/days",
        params={"from": "2026-11-01", "to": "2026-11-30"},
        headers={"If-None-Match": response.headers["ETag"]},
    )
    assert not_modified.status_code == 304
    assert not not_modified.content


async def test_story_filters_combine_with_and(client, published_report) -> None:
    response = await client.get(
        "/v1/days/2026-11-12/stories",
        params={"direction": "negative", "region": "germany"},
    )
    assert response.status_code == 200
    assert_valid(response.json(), "StoryCollection")
    assert len(response.json()["stories"]) == 1
    assert all(story["direction"] == "negative" for story in response.json()["stories"])
    assert all(story["region"] == "germany" for story in response.json()["stories"])
    invalid = await client.get("/v1/days/2026-11-12/stories", params={"direction": "sideways"})
    assert invalid.status_code == 422


async def test_superseded_revision_and_its_stories_are_invisible(
    client,
    published_report,
) -> None:
    response = await client.get(f"/v1/stories/{published_report.superseded_story_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_current_story_returns_attribution_snapshot(client, published_report) -> None:
    story_id = published_report.current_story_ids[0]
    response = await client.get(f"/v1/stories/{story_id}")
    assert response.status_code == 200
    assert_valid(response.json(), "Story")
    assert response.json()["sources"][0]["publisher"]
    assert response.json()["sources"][0]["attribution"]


async def test_etag_conditional_handles_multiple_weak_and_mismatched_tags(
    client,
    published_report,
) -> None:
    latest = await client.get("/v1/days/latest")
    etag = latest.headers["ETag"]

    multiple = await client.get(
        "/v1/days/latest", headers={"If-None-Match": f'"unrelated", {etag}'}
    )
    assert multiple.status_code == 304

    weak = await client.get("/v1/days/latest", headers={"If-None-Match": f"W/{etag}"})
    assert weak.status_code == 304

    wildcard = await client.get("/v1/days/latest", headers={"If-None-Match": "*"})
    assert wildcard.status_code == 304

    mismatched = await client.get("/v1/days/latest", headers={"If-None-Match": '"nope"'})
    assert mismatched.status_code == 200
    assert_valid(mismatched.json(), "DailyReport")


async def test_rate_limit_returns_429_with_retry_after(
    published_report,
    test_database_url: str,
) -> None:
    from asgi_lifespan import LifespanManager
    from httpx import ASGITransport, AsyncClient

    from daily_signal.core.config import Settings
    from daily_signal.main import create_app

    app = create_app(
        Settings(
            database_url=test_database_url,
            rate_limit_per_minute=2,
        )
    )
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        assert (await client.get("/v1/days/2026-11-12")).status_code == 200
        assert (await client.get("/v1/days/2026-11-12")).status_code == 200
        limited = await client.get("/v1/days/2026-11-12")
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) >= 1
    assert_valid(limited.json(), "ApiError")
