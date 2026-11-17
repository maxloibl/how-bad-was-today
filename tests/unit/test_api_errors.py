"""Unit tests for the shared HTTP error vocabulary."""

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from daily_signal.api.errors import HTTP_STATUS_CODES, not_found, register_exception_handlers


def test_status_code_map_covers_middleware_and_handler_codes() -> None:
    assert HTTP_STATUS_CODES[400] == "bad_request"
    assert HTTP_STATUS_CODES[404] == "not_found"
    assert HTTP_STATUS_CODES[405] == "method_not_allowed"
    assert HTTP_STATUS_CODES[422] == "invalid_parameter"
    assert HTTP_STATUS_CODES[429] == "rate_limited"


async def test_not_found_helper_builds_contract_envelope() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/missing")
    async def missing() -> None:
        raise not_found("Story not found or not published.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["message"] == "Story not found or not published."
