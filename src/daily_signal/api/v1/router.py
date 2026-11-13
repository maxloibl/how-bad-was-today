"""Versioned public API router.

Routes are added by later tasks; this module only establishes the ``/v1``
prefix so every public endpoint shares a consistent base path.
"""

from fastapi import APIRouter

api_router = APIRouter(prefix="/v1")
