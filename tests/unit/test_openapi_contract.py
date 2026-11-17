import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from daily_signal.core.config import Settings
from daily_signal.main import create_app
from tests.contract.validation import CONTRACT

#: A URL that is never dialed: this test only inspects the generated schema.
UNUSED_DATABASE_URL = "postgresql+asyncpg://unused:unused@127.0.0.1:1/unused"


@contextmanager
def _app() -> Iterator[FastAPI]:
    """Build the app and always dispose its engine, even on assertion failure."""
    app = create_app(Settings(database_url=UNUSED_DATABASE_URL))
    try:
        yield app
    finally:
        asyncio.run(cast(AsyncEngine, app.state.engine).dispose())


def test_generated_openapi_matches_contract_route_inventory() -> None:
    with _app() as app:
        generated = app.openapi()
    contract_routes = {
        (path, method) for path, item in CONTRACT["paths"].items() for method in item
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
            == CONTRACT["paths"][path][method]["operationId"]
        )
