"""Unit tests for the rate-limit middleware's internal bookkeeping."""

from starlette.requests import Request
from starlette.types import Receive, Scope, Send

from daily_signal.api.middleware import _WINDOW_SECONDS, RateLimitMiddleware


async def _noop_app(scope: Scope, receive: Receive, send: Send) -> None:
    """An ASGI app that is never invoked by these tests."""
    raise NotImplementedError


def _request(host: str, port: int) -> Request:
    scope: Scope = {"type": "http", "client": (host, port)}
    return Request(scope)


def _middleware() -> RateLimitMiddleware:
    return RateLimitMiddleware(_noop_app, rate_limit_per_minute=10)


def test_client_key_ignores_ephemeral_source_port() -> None:
    first = RateLimitMiddleware._client_key(_request("203.0.113.7", 51000))
    second = RateLimitMiddleware._client_key(_request("203.0.113.7", 52000))
    assert first == second == "203.0.113.7"


def test_client_key_without_client_is_unknown() -> None:
    assert RateLimitMiddleware._client_key(Request({"type": "http"})) == "unknown"


def test_purge_expired_removes_only_stale_windows() -> None:
    middleware = _middleware()
    middleware._windows = {
        "stale": (100.0, 5),
        "fresh": (100.0 + _WINDOW_SECONDS / 2, 5),
    }
    middleware._purge_expired(100.0 + _WINDOW_SECONDS)
    assert "stale" not in middleware._windows
    assert "fresh" in middleware._windows
