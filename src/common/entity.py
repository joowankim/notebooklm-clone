"""Base Entity class for domain models."""

import datetime

import pydantic


class Entity(pydantic.BaseModel):
    """Base class for all domain entities.

    Entities are immutable by default. State changes should return new instances.
    """

    model_config = pydantic.ConfigDict(
        frozen=True,
        extra="forbid",
    )

    id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
