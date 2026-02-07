"""Chunk REST API router."""

import fastapi
from dependency_injector.wiring import Provide, inject

from src.chunk.handler import handlers
from src.chunk.schema import response
from src.dependency import container as container_module

router = fastapi.APIRouter(prefix="/chunks", tags=["chunks"])


@router.get(
    "/{chunk_id}",
    response_model=response.ChunkDetail,
)
@inject
async def get_chunk(
    chunk_id: str,
    handler: handlers.GetChunkHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.chunk.handler.get_chunk_handler]
    ),
) -> response.ChunkDetail:
    """Get chunk by ID."""
    return await handler.handle(chunk_id)


@router.get(
    "/document/{document_id}",
    response_model=list[response.ChunkDetail],
)
@inject
async def list_chunks_by_document(
    document_id: str,
    handler: handlers.ListChunksByDocumentHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.chunk.handler.list_chunks_by_document_handler]
    ),
) -> list[response.ChunkDetail]:
    """List chunks for a document."""
    return await handler.handle(document_id)
