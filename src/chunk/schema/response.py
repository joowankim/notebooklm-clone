"""Chunk response schemas (output DTOs)."""

import datetime
from typing import Self

import pydantic

from src.chunk.domain import model


class ChunkDetail(pydantic.BaseModel):
    """Detailed chunk response."""

    id: str
    document_id: str
    content: str
    char_start: int
    char_end: int
    chunk_index: int
    token_count: int
    created_at: datetime.datetime

    @classmethod
    def from_entity(cls, entity: model.Chunk) -> Self:
        """Create response from domain entity."""
        return cls(
            id=entity.id,
            document_id=entity.document_id,
            content=entity.content,
            char_start=entity.char_start,
            char_end=entity.char_end,
            chunk_index=entity.chunk_index,
            token_count=entity.token_count,
            created_at=entity.created_at,
        )


class ChunkWithScore(pydantic.BaseModel):
    """Chunk with similarity score for search results."""

    chunk: ChunkDetail
    score: float

    @classmethod
    def from_entity_and_score(cls, entity: model.Chunk, score: float) -> Self:
        """Create from entity and score."""
        return cls(
            chunk=ChunkDetail.from_entity(entity),
            score=score,
        )
