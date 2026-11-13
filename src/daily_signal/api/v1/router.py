"""Versioned public API router.

Establishes the ``/v1`` prefix and includes the published report, story,
source, and methodology routes. ``/v1/days/latest`` is registered before
``/v1/days/{date}`` (inside ``days_router``) so the literal path wins.
"""

from fastapi import APIRouter

from daily_signal.api.v1.days import router as days_router
from daily_signal.api.v1.methodology import router as methodology_router
from daily_signal.api.v1.sources import router as sources_router
from daily_signal.api.v1.stories import router as stories_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(days_router)
api_router.include_router(stories_router)
api_router.include_router(sources_router)
api_router.include_router(methodology_router)
