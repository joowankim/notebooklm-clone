"""Chunk domain entity."""

import datetime
import uuid
from typing import Self

import pydantic

from src.common import types as common_types


class Chunk(pydantic.BaseModel):
    """Chunk entity representing a piece of document content.

    Immutable: all state changes return new instances.
    """

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    document_id: str
    content: str
    char_start: int
    char_end: int
    chunk_index: int
    token_count: int
    embedding: list[float] | None = None
    created_at: datetime.datetime

    @classmethod
    def create(
        cls,
        document_id: str,
        content: str,
        char_start: int,
        char_end: int,
        chunk_index: int,
        token_count: int,
        embedding: list[float] | None = None,
    ) -> Self:
        """Factory method to create a new chunk."""
        return cls(
            id=uuid.uuid4().hex,
            document_id=document_id,
            content=content,
            char_start=char_start,
            char_end=char_end,
            chunk_index=chunk_index,
            token_count=token_count,
            embedding=embedding,
            created_at=common_types.utc_now(),
        )

    def with_embedding(self, embedding: list[float]) -> Self:
        """Return chunk with embedding set."""
        return self.model_copy(update={"embedding": embedding})
