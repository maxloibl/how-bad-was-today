"""Shared Pydantic base model with camelCase JSON aliases."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    """Base for all public API DTOs.

    Attributes stay snake_case in Python while serialising to camelCase in
    JSON. ``populate_by_name`` also accepts the snake_case names on input so
    internal callers and tests never need to know the wire alias.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
