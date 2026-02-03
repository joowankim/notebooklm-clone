"""Notebook response schemas (output DTOs)."""

import datetime
from typing import Self

import pydantic

from src.notebook.domain.model import Notebook


class NotebookId(pydantic.BaseModel):
    """Response containing notebook ID."""

    id: str


class NotebookDetail(pydantic.BaseModel):
    """Detailed notebook response."""

    id: str
    name: str
    description: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: Notebook) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
