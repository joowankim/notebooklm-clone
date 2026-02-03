"""Notebook domain entity."""

import datetime
import uuid
from typing import Self

import pydantic

from src.common.types import utc_now


class Notebook(pydantic.BaseModel):
    """Notebook entity for organizing research sources.

    Immutable: all state changes return new instances.
    """

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    description: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def create(cls, name: str, description: str | None = None) -> Self:
        """Factory method to create a new notebook."""
        now = utc_now()
        return cls(
            id=uuid.uuid4().hex,
            name=name,
            description=description,
            created_at=now,
            updated_at=now,
        )

    def update(self, name: str | None = None, description: str | None = None) -> Self:
        """Return new notebook with updated fields."""
        return self.model_copy(
            update={
                "name": name if name is not None else self.name,
                "description": description if description is not None else self.description,
                "updated_at": utc_now(),
            }
        )
