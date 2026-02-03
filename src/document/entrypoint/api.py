"""Document REST API router."""

import http

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from src.common import PaginationSchema
from src.dependency.container import ApplicationContainer
from src.document.handler import handlers
from src.document.schema import command, query, response

router = APIRouter(prefix="/notebooks/{notebook_id}/sources", tags=["sources"])


@router.post(
    "",
    response_model=response.DocumentId,
    status_code=http.HTTPStatus.CREATED,
)
@inject
async def add_source(
    notebook_id: str,
    cmd: command.AddSource,
    handler: handlers.AddSourceHandler = Depends(
        Provide[ApplicationContainer.document.handler.add_source_handler]
    ),
) -> response.DocumentId:
    """Add a source URL to a notebook."""
    return await handler.handle(notebook_id, cmd)


@router.get(
    "",
    response_model=PaginationSchema[response.DocumentDetail],
)
@inject
async def list_sources(
    notebook_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    handler: handlers.ListSourcesHandler = Depends(
        Provide[ApplicationContainer.document.handler.list_sources_handler]
    ),
) -> PaginationSchema[response.DocumentDetail]:
    """List sources in a notebook with pagination."""
    qry = query.ListSources(notebook_id=notebook_id, page=page, size=size)
    return await handler.handle(qry)


# Document detail endpoint (under different prefix)
document_router = APIRouter(prefix="/documents", tags=["documents"])


@document_router.get(
    "/{document_id}",
    response_model=response.DocumentDetail,
)
@inject
async def get_document(
    document_id: str,
    handler: handlers.GetDocumentHandler = Depends(
        Provide[ApplicationContainer.document.handler.get_document_handler]
    ),
) -> response.DocumentDetail:
    """Get document by ID."""
    return await handler.handle(document_id)
