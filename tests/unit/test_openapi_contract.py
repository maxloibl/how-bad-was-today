from daily_signal.core.config import Settings
from daily_signal.main import create_app
from tests.contract.validation import CONTRACT

#: A URL that is never dialed: this test only inspects the generated schema.
UNUSED_DATABASE_URL = "postgresql+asyncpg://unused:unused@127.0.0.1:1/unused"


def test_generated_openapi_matches_contract_route_inventory() -> None:
    app = create_app(Settings(database_url=UNUSED_DATABASE_URL))
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
