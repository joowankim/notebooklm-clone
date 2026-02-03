"""Chunk REST API router."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.chunk.handler import handlers
from src.chunk.schema.response import ChunkDetail
from src.dependency.container import ApplicationContainer

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.get(
    "/{chunk_id}",
    response_model=ChunkDetail,
)
@inject
async def get_chunk(
    chunk_id: str,
    handler: handlers.GetChunkHandler = Depends(
        Provide[ApplicationContainer.chunk.handler.get_chunk_handler]
    ),
) -> ChunkDetail:
    """Get chunk by ID."""
    return await handler.handle(chunk_id)


@router.get(
    "/document/{document_id}",
    response_model=list[ChunkDetail],
)
@inject
async def list_chunks_by_document(
    document_id: str,
    handler: handlers.ListChunksByDocumentHandler = Depends(
        Provide[ApplicationContainer.chunk.handler.list_chunks_by_document_handler]
    ),
) -> list[ChunkDetail]:
    """List chunks for a document."""
    return await handler.handle(document_id)
