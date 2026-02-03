"""Chunk repository implementation with vector search."""

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

from src.chunk.domain.mapper import ChunkMapper
from src.chunk.domain.model import Chunk
from src.infrastructure.models.chunk import ChunkSchema


class ChunkRepository:
    """Repository for Chunk persistence with vector search capabilities."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = ChunkMapper()

    async def find_by_id(self, id: str) -> Chunk | None:
        """Find chunk by ID."""
        stmt = sqlalchemy.select(ChunkSchema).where(ChunkSchema.id == id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: Chunk) -> Chunk:
        """Save chunk (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._mapper.to_entity(merged)

    async def save_batch(self, entities: list[Chunk]) -> list[Chunk]:
        """Save multiple chunks efficiently."""
        if not entities:
            return []

        records = [self._mapper.to_record(entity) for entity in entities]
        for record in records:
            await self._session.merge(record)
        await self._session.flush()
        return entities

    async def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks for a document."""
        stmt = sqlalchemy.delete(ChunkSchema).where(
            ChunkSchema.document_id == document_id
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    async def list_by_document(self, document_id: str) -> list[Chunk]:
        """List chunks for a document ordered by chunk_index."""
        stmt = (
            sqlalchemy.select(ChunkSchema)
            .where(ChunkSchema.document_id == document_id)
            .order_by(ChunkSchema.chunk_index)
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._mapper.to_entity(record) for record in records]

    async def search_similar(
        self,
        embedding: list[float],
        document_ids: list[str],
        limit: int = 10,
    ) -> list[tuple[Chunk, float]]:
        """Search for similar chunks using cosine similarity.

        Args:
            embedding: Query embedding vector.
            document_ids: List of document IDs to search within.
            limit: Maximum number of results.

        Returns:
            List of (Chunk, similarity_score) tuples ordered by similarity.
        """
        if not document_ids:
            return []

        # Use pgvector cosine distance operator (<=>)
        # Lower distance = higher similarity
        distance = ChunkSchema.embedding.cosine_distance(embedding)

        stmt = (
            sqlalchemy.select(ChunkSchema, distance.label("distance"))
            .where(
                ChunkSchema.document_id.in_(document_ids),
                ChunkSchema.embedding.isnot(None),
            )
            .order_by(distance)
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        # Convert distance to similarity score (1 - distance for cosine)
        return [
            (self._mapper.to_entity(row.ChunkSchema), 1 - row.distance)
            for row in rows
        ]

    async def search_similar_in_notebook(
        self,
        embedding: list[float],
        notebook_id: str,
        limit: int = 10,
    ) -> list[tuple[Chunk, float]]:
        """Search for similar chunks across all documents in a notebook.

        Args:
            embedding: Query embedding vector.
            notebook_id: Notebook ID to search within.
            limit: Maximum number of results.

        Returns:
            List of (Chunk, similarity_score) tuples ordered by similarity.
        """
        from src.infrastructure.models.document import DocumentSchema

        distance = ChunkSchema.embedding.cosine_distance(embedding)

        stmt = (
            sqlalchemy.select(ChunkSchema, distance.label("distance"))
            .join(DocumentSchema, ChunkSchema.document_id == DocumentSchema.id)
            .where(
                DocumentSchema.notebook_id == notebook_id,
                ChunkSchema.embedding.isnot(None),
            )
            .order_by(distance)
            .limit(limit)
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [
            (self._mapper.to_entity(row.ChunkSchema), 1 - row.distance)
            for row in rows
        ]
