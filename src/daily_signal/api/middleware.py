"""Request-ID and fixed-window rate-limit middleware."""

from __future__ import annotations

import math
import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from daily_signal.api.schemas.errors import ApiError, ApiErrorBody

_WINDOW_SECONDS = 60.0


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign a UUID4 to ``request.state.request_id`` and return ``X-Request-ID``."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory fixed-window limiter for ``/v1/`` routes only.

    ``rate_limit_per_minute`` of ``0`` disables limiting. Each client address
    gets its own 60-second window; once exhausted, requests are rejected with a
    ``429`` envelope and a ``Retry-After`` header.
    """

    def __init__(self, app: ASGIApp, rate_limit_per_minute: int) -> None:
        super().__init__(app)
        self._limit = rate_limit_per_minute
        self._windows: dict[str, tuple[float, int]] = {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._limit <= 0:
            return await call_next(request)
        if not request.url.path.startswith("/v1/"):
            return await call_next(request)

        key = self._client_key(request)
        now = time.monotonic()
        window_start, count = self._windows.get(key, (now, 0))
        if now - window_start >= _WINDOW_SECONDS:
            window_start = now
            count = 0
        if count >= self._limit:
            return self._rate_limited(request, window_start, now)
        self._windows[key] = (window_start, count + 1)
        return await call_next(request)

    @staticmethod
    def _client_key(request: Request) -> str:
        if request.client is None:
            return "unknown"
        return f"{request.client.host}:{request.client.port}"

    def _rate_limited(self, request: Request, window_start: float, now: float) -> JSONResponse:
        remaining = window_start + _WINDOW_SECONDS - now
        retry_after = max(1, math.ceil(remaining))
        body = ApiErrorBody(
            code="rate_limited",
            message="Rate limit exceeded.",
            request_id=request.state.request_id,
        )
        response = JSONResponse(
            status_code=429,
            content=ApiError(error=body).model_dump(by_alias=True),
        )
        response.headers["Retry-After"] = str(retry_after)
        return response
