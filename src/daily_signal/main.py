"""FastAPI application factory for the public read-only API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from daily_signal.api.errors import ApiErrorException, register_exception_handlers
from daily_signal.api.middleware import RateLimitMiddleware, RequestIdMiddleware
from daily_signal.api.schemas.health import HealthStatus
from daily_signal.api.v1.router import api_router
from daily_signal.application.methodology import load_methodology
from daily_signal.core.config import Settings
from daily_signal.core.logging import configure_logging
from daily_signal.infrastructure.db.session import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup/shutdown for the application.

    Startup loads and validates the pinned methodology document into
    ``app.state.methodology`` and performs no schema work: migrations remain the
    only source of schema. Shutdown disposes the engine's connection pool, even
    when the application raised during its lifetime.
    """
    settings = cast(Settings, app.state.settings)
    app.state.methodology = load_methodology(settings.methodology_config_path)
    try:
        yield
    finally:
        await cast(AsyncEngine, app.state.engine).dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application with the public router and health routes."""
    resolved = settings or Settings()
    configure_logging(resolved.log_level)

    engine = create_engine(resolved)
    session_factory = create_session_factory(engine)

    app = FastAPI(
        title="Daily Signal Public API",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.settings = resolved
    app.state.engine = engine
    app.state.session_factory = session_factory

    # Middleware order: ``add_middleware`` prepends, so the last one added is
    # outermost. RequestIdMiddleware is added last so it wraps everything —
    # including CORSMiddleware, whose preflights it must be able to label and
    # normalise. RateLimitMiddleware is added first so a request ID always
    # exists before any rate-limit decision is made.
    app.add_middleware(RateLimitMiddleware, rate_limit_per_minute=resolved.rate_limit_per_minute)

    if resolved.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=resolved.cors_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(RequestIdMiddleware)

    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get(
        "/health/live",
        response_model=HealthStatus,
        tags=["Operations"],
        operation_id="getLiveness",
    )
    async def health_live() -> HealthStatus:
        """Liveness: never touches the database."""
        return HealthStatus(status="ok")

    @app.get(
        "/health/ready",
        response_model=HealthStatus,
        tags=["Operations"],
        operation_id="getReadiness",
    )
    async def health_ready(request: Request) -> HealthStatus:
        """Readiness: verifies database connectivity with ``SELECT 1``."""
        factory = cast(async_sessionmaker[AsyncSession], request.app.state.session_factory)
        try:
            async with factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as exc:
            raise ApiErrorException(
                503, "service_unavailable", "Service temporarily unavailable."
            ) from exc
        return HealthStatus(status="ok")

    return app


app = create_app()
