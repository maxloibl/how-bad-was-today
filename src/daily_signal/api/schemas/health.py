"""Health-check response DTOs."""

from typing import Literal

from pydantic import ConfigDict

from daily_signal.api.schemas.base import ApiModel


class HealthStatus(ApiModel):
    """``{"status": "ok"}`` returned by liveness and readiness."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
