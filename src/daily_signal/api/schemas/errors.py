"""The standard API error envelope.

Every error response is ``{"error": {"code", "message", "requestId"}}``,
matching ``contracts/openapi.yaml`` exactly. The inner object has no extra
properties allowed, mirroring ``additionalProperties: false``.
"""

from pydantic import ConfigDict

from daily_signal.api.schemas.base import ApiModel


class ApiErrorBody(ApiModel):
    """The ``error`` payload carried by every error response."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str


class ApiError(ApiModel):
    """The full error envelope."""

    model_config = ConfigDict(extra="forbid")

    error: ApiErrorBody
