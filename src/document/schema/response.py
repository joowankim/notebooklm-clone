"""Document response schemas (output DTOs)."""

import datetime
from typing import Self

import pydantic

from src.document.domain import model


class DocumentId(pydantic.BaseModel):
    """Response containing document ID."""

    id: str


class DocumentDetail(pydantic.BaseModel):
    """Detailed document response."""

    id: str
    notebook_id: str
    url: str
    title: str | None
    status: str
    error_message: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: model.Document) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            notebook_id=entity.notebook_id,
            url=entity.url,
            title=entity.title,
            status=entity.status.value,
            error_message=entity.error_message,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
