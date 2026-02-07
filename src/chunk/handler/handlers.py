"""Chunk command and query handlers."""

from src import exceptions
from src.chunk.adapter import repository as chunk_repository_module
from src.chunk.schema import response


class GetChunkHandler:
    """Handler for getting chunk details."""

    def __init__(self, repository: chunk_repository_module.ChunkRepository) -> None:
        self._repository = repository

    async def handle(self, chunk_id: str) -> response.ChunkDetail:
        """Get chunk by ID."""
        chunk = await self._repository.find_by_id(chunk_id)
        if chunk is None:
            raise exceptions.NotFoundError(f"Chunk not found: {chunk_id}")
        return response.ChunkDetail.from_entity(chunk)


class ListChunksByDocumentHandler:
    """Handler for listing chunks by document."""

    def __init__(self, repository: chunk_repository_module.ChunkRepository) -> None:
        self._repository = repository

    async def handle(self, document_id: str) -> list[response.ChunkDetail]:
        """List chunks for a document."""
        chunks = await self._repository.list_by_document(document_id)
        return [response.ChunkDetail.from_entity(chunk) for chunk in chunks]
