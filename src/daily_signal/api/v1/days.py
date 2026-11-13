"""Public ``/v1/days`` routes: calendar, latest report, report by date, stories."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request, Response

from daily_signal.api.dependencies import get_report_repository
from daily_signal.api.errors import ApiErrorException
from daily_signal.api.etag import etag_matches, make_days_etag, make_report_etag
from daily_signal.api.schemas.days import DailyReport, DayCollection
from daily_signal.api.schemas.mapping import daily_report, day_collection, story_collection
from daily_signal.api.schemas.stories import StoryCollection
from daily_signal.application.ports.repositories import DailyReportRepository
from daily_signal.application.queries.get_daily_report import (
    get_daily_report,
    get_latest_daily_report,
)
from daily_signal.application.queries.list_daily_reports import list_daily_reports
from daily_signal.domain.enums import Category, Direction, Region

router = APIRouter(tags=["Days"])

#: The contract caps an inclusive calendar range at 366 days.
_MAX_RANGE_DAYS = 366


def _not_found(message: str) -> ApiErrorException:
    return ApiErrorException(404, "not_found", message)


@router.get("/days", response_model=DayCollection, operation_id="listDays")
async def list_days(
    request: Request,
    response: Response,
    repository: Annotated[DailyReportRepository, Depends(get_report_repository)],
    from_date: Annotated[date, Query(alias="from")],
    to_date: Annotated[date, Query(alias="to")],
) -> DayCollection | Response:
    """List published days in an inclusive range, ascending by date."""
    if from_date > to_date:
        raise ApiErrorException(400, "invalid_date_range", "`from` must not be after `to`.")
    if (to_date - from_date).days + 1 > _MAX_RANGE_DAYS:
        raise ApiErrorException(400, "date_range_too_large", "Date range must not exceed 366 days.")

    records = await list_daily_reports(repository, from_date, to_date)
    etag = make_days_etag(from_date, to_date, records)
    if etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag})
    response.headers["ETag"] = etag
    return day_collection(from_date, to_date, records)


@router.get("/days/latest", response_model=DailyReport, operation_id="getLatestDay")
async def get_latest_day(
    request: Request,
    response: Response,
    repository: Annotated[DailyReportRepository, Depends(get_report_repository)],
) -> DailyReport | Response:
    """Return the most recent current published report, if any."""
    record = await get_latest_daily_report(repository)
    if record is None:
        raise _not_found("No published report found.")
    etag = make_report_etag(record.id, record.revision)
    if etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag})
    response.headers["ETag"] = etag
    return daily_report(record)


@router.get("/days/{date}", response_model=DailyReport, operation_id="getDay")
async def get_day(
    request: Request,
    response: Response,
    repository: Annotated[DailyReportRepository, Depends(get_report_repository)],
    date: Annotated[date, Path()],
) -> DailyReport | Response:
    """Return the current published report for a Berlin-local calendar date."""
    record = await get_daily_report(repository, date)
    if record is None:
        raise _not_found("Report not found or not published.")
    etag = make_report_etag(record.id, record.revision)
    if etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers={"ETag": etag})
    response.headers["ETag"] = etag
    return daily_report(record)


@router.get("/days/{date}/stories", response_model=StoryCollection, operation_id="listDayStories")
async def list_day_stories(
    repository: Annotated[DailyReportRepository, Depends(get_report_repository)],
    date: Annotated[date, Path()],
    direction: Annotated[Direction | None, Query()] = None,
    category: Annotated[Category | None, Query()] = None,
    region: Annotated[Region | None, Query()] = None,
) -> StoryCollection:
    """List stories in a day's current published report, filtered with AND."""
    record = await get_daily_report(repository, date)
    if record is None:
        raise _not_found("Report not found or not published.")

    stories = [
        story
        for story in record.stories
        if (direction is None or story.direction == direction)
        and (category is None or story.category == category)
        and (region is None or story.region == region)
    ]
    return story_collection(date, stories)
