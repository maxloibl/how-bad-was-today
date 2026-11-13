import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from daily_signal.core.config import Settings
from daily_signal.main import create_app

pytestmark = pytest.mark.integration

CORS_ORIGIN = "https://app.example"


def _cors_app(test_database_url: str) -> FastAPI:
    return create_app(
        Settings(
            database_url=test_database_url,
            rate_limit_per_minute=0,
            cors_origins=[CORS_ORIGIN],
        )
    )


async def test_live_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


async def test_ready_returns_ok_when_database_is_available(client: AsyncClient) -> None:
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_returns_503_when_database_is_unavailable(migrated_database: str) -> None:
    app = create_app(
        Settings(
            database_url="postgresql+asyncpg://nobody:nobody@127.0.0.1:1/nothing",
            rate_limit_per_minute=0,
        )
    )
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        response = await client.get("/health/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "service_unavailable"
    assert body["error"]["requestId"] == response.headers["X-Request-ID"]


async def test_unknown_route_uses_error_envelope(client: AsyncClient) -> None:
    response = await client.get("/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"]
    assert body["error"]["requestId"] == response.headers["X-Request-ID"]


async def test_method_not_allowed_keeps_allow_header(client: AsyncClient) -> None:
    response = await client.post("/health/live")
    assert response.status_code == 405
    assert "GET" in response.headers["allow"]
    body = response.json()
    assert body["error"]["code"] == "method_not_allowed"
    assert body["error"]["requestId"] == response.headers["X-Request-ID"]


async def test_cors_preflight_allowed_carries_headers_and_request_id(
    test_database_url: str,
) -> None:
    app = _cors_app(test_database_url)
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        response = await client.options(
            "/v1/days",
            headers={
                "Origin": CORS_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == CORS_ORIGIN
    assert response.headers["X-Request-ID"]


async def test_cors_preflight_disallowed_uses_error_envelope(
    test_database_url: str,
) -> None:
    app = _cors_app(test_database_url)
    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        response = await client.options(
            "/v1/days",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "bad_request"
    assert body["error"]["message"]
    assert body["error"]["requestId"] == response.headers["X-Request-ID"]
