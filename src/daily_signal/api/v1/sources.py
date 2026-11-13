"""Public ``/v1/sources`` route: currently approved news sources."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from daily_signal.api.dependencies import get_source_repository
from daily_signal.api.schemas.sources import SourceCollection, source_collection
from daily_signal.application.ports.repositories import SourceRepository

router = APIRouter(tags=["Sources"])


@router.get("/sources", response_model=SourceCollection, operation_id="listSources")
async def list_sources(
    repository: Annotated[SourceRepository, Depends(get_source_repository)],
) -> SourceCollection:
    """List sources that are approved, enabled and have an approved permission."""
    return source_collection(await repository.list_approved())
