"""API error types and exception-to-envelope translation."""

from __future__ import annotations

import uuid
from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from daily_signal.api.schemas.errors import ApiError, ApiErrorBody

#: Shared status-to-code vocabulary for HTTP exceptions raised by the app or
#: by ASGI middleware that bypasses the exception handlers. Unmapped statuses
#: fall back to the generic ``error`` code.
HTTP_STATUS_CODES: dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "invalid_parameter",
    429: "rate_limited",
}


class ApiErrorException(Exception):
    """Raise to abort a request with the standard error envelope."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(message: str) -> ApiErrorException:
    """Build the standard 404 error for a missing or unpublished resource."""
    return ApiErrorException(404, "not_found", message)


def _request_id(request: Request) -> str:
    """Return the per-request ID, generating one if middleware has not set it."""
    request_id = cast("str | None", getattr(request.state, "request_id", None))
    if request_id is None:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
    return request_id


def _envelope(request: Request, code: str, message: str) -> dict[str, object]:
    """Build the ``{"error": {...}}`` payload for the current request."""
    body = ApiErrorBody(code=code, message=message, request_id=_request_id(request))
    return ApiError(error=body).model_dump(by_alias=True)


def register_exception_handlers(app: FastAPI) -> None:
    """Register every exception handler on ``app``."""

    @app.exception_handler(ApiErrorException)
    async def _handle_api_error(request: Request, exc: ApiErrorException) -> JSONResponse:
        content = _envelope(request, exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # The message is intentionally generic: raw input must never be echoed.
        content = _envelope(request, "invalid_parameter", "Invalid request parameter.")
        return JSONResponse(status_code=422, content=content)

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = HTTP_STATUS_CODES.get(exc.status_code, "error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        content = _envelope(request, code, message)
        # Preserve protocol-required headers (e.g. ``Allow`` on a 405) that
        # Starlette attached to the original HTTP exception.
        return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)

    @app.exception_handler(Exception)
    async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
        content = _envelope(request, "internal_error", "Internal server error.")
        response = JSONResponse(status_code=500, content=content)
        # This handler runs outside RequestIdMiddleware (it is invoked by
        # ServerErrorMiddleware), so it sets the header itself to keep the body
        # and header request IDs consistent.
        response.headers["X-Request-ID"] = _request_id(request)
        return response
