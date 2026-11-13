"""Public ``/v1/methodology`` route: the pinned public methodology."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Request

from daily_signal.api.schemas.methodology import Methodology, methodology
from daily_signal.application.methodology import MethodologyConfig

router = APIRouter(tags=["Methodology"])


@router.get("/methodology", response_model=Methodology, operation_id="getMethodology")
async def get_methodology(request: Request) -> Methodology:
    """Return the methodology document loaded once during application startup."""
    config = cast(MethodologyConfig, request.app.state.methodology)
    return methodology(config)
