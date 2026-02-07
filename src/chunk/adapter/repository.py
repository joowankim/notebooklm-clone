"""Chunk repository implementation with vector search."""

import sqlalchemy
import sqlalchemy.ext.asyncio

from src.chunk.domain import mapper as chunk_mapper_module
from src.chunk.domain import model
from src.infrastructure.models import chunk as chunk_schema
from src.infrastructure.models import document as document_schema


class ChunkRepository:
    """Repository for Chunk persistence with vector search capabilities."""

    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self._session = session
        self._mapper = chunk_mapper_module.ChunkMapper()

    async def find_by_id(self, id: str) -> model.Chunk | None:
        """Find chunk by ID."""
        stmt = sqlalchemy.select(chunk_schema.ChunkSchema).where(chunk_schema.ChunkSchema.id == id)
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return self._mapper.to_entity(record)

    async def save(self, entity: model.Chunk) -> model.Chunk:
        """Save chunk (insert or update)."""
        record = self._mapper.to_record(entity)
        merged = await self._session.merge(record)
        await self._session.flush()
        return self._mapper.to_entity(merged)

    async def save_batch(self, entities: list[model.Chunk]) -> list[model.Chunk]:
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
        stmt = sqlalchemy.delete(chunk_schema.ChunkSchema).where(
            chunk_schema.ChunkSchema.document_id == document_id
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    async def list_by_document(self, document_id: str) -> list[model.Chunk]:
        """List chunks for a document ordered by chunk_index."""
        stmt = (
            sqlalchemy.select(chunk_schema.ChunkSchema)
            .where(chunk_schema.ChunkSchema.document_id == document_id)
            .order_by(chunk_schema.ChunkSchema.chunk_index)
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()
        return [self._mapper.to_entity(record) for record in records]

    async def search_similar(
        self,
        embedding: list[float],
        document_ids: list[str],
        limit: int = 10,
    ) -> list[tuple[model.Chunk, float]]:
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
        distance = chunk_schema.ChunkSchema.embedding.cosine_distance(embedding)

        stmt = (
            sqlalchemy.select(chunk_schema.ChunkSchema, distance.label("distance"))
            .where(
                chunk_schema.ChunkSchema.document_id.in_(document_ids),
                chunk_schema.ChunkSchema.embedding.isnot(None),
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
    ) -> list[tuple[model.Chunk, float]]:
        """Search for similar chunks across all documents in a notebook.

        Args:
            embedding: Query embedding vector.
            notebook_id: Notebook ID to search within.
            limit: Maximum number of results.

        Returns:
            List of (Chunk, similarity_score) tuples ordered by similarity.
        """
        distance = chunk_schema.ChunkSchema.embedding.cosine_distance(embedding)

        stmt = (
            sqlalchemy.select(chunk_schema.ChunkSchema, distance.label("distance"))
            .join(document_schema.DocumentSchema, chunk_schema.ChunkSchema.document_id == document_schema.DocumentSchema.id)
            .where(
                document_schema.DocumentSchema.notebook_id == notebook_id,
                chunk_schema.ChunkSchema.embedding.isnot(None),
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
