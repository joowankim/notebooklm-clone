"""Mapper between Chunk entity and ORM schema."""

from src.chunk.domain.model import Chunk
from src.infrastructure.models.chunk import ChunkSchema


class ChunkMapper:
    """Maps between Chunk domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: ChunkSchema) -> Chunk:
        """Convert ORM record to domain entity."""
        embedding = list(record.embedding) if record.embedding is not None else None
        return Chunk(
            id=record.id,
            document_id=record.document_id,
            content=record.content,
            char_start=record.char_start,
            char_end=record.char_end,
            chunk_index=record.chunk_index,
            token_count=record.token_count,
            embedding=embedding,
            created_at=record.created_at,
        )

    @staticmethod
    def to_record(entity: Chunk) -> ChunkSchema:
        """Convert domain entity to ORM record."""
        return ChunkSchema(
            id=entity.id,
            document_id=entity.document_id,
            content=entity.content,
            char_start=entity.char_start,
            char_end=entity.char_end,
            chunk_index=entity.chunk_index,
            token_count=entity.token_count,
            embedding=entity.embedding,
            created_at=entity.created_at,
        )
