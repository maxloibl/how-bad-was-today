"""Versioned public API router.

Establishes the ``/v1`` prefix and includes the published report and story
routes. ``/v1/days/latest`` is registered before ``/v1/days/{date}`` (inside
``days_router``) so the literal path wins.
"""

from fastapi import APIRouter

from daily_signal.api.v1.days import router as days_router
from daily_signal.api.v1.stories import router as stories_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(days_router)
api_router.include_router(stories_router)
