"""Public ``/v1/stories`` route: a single story snapshot."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path

from daily_signal.api.dependencies import get_report_repository
from daily_signal.api.errors import ApiErrorException
from daily_signal.api.schemas.mapping import story
from daily_signal.api.schemas.stories import Story
from daily_signal.application.ports.repositories import DailyReportRepository
from daily_signal.application.queries.get_daily_report import get_story

router = APIRouter(tags=["Stories"])


@router.get("/stories/{id}", response_model=Story, operation_id="getStory")
async def get_story_by_id(
    repository: Annotated[DailyReportRepository, Depends(get_report_repository)],
    story_id: Annotated[UUID, Path(alias="id")],
) -> Story:
    """Return a story from a current published report, or 404."""
    record = await get_story(repository, story_id)
    if record is None:
        raise ApiErrorException(404, "not_found", "Story not found or not published.")
    return story(record)
