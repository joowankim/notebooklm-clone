"""Query REST API router."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Request

from src.common.rate_limit import QUERY_RATE, limiter
from src.dependency.container import ApplicationContainer
from src.query.handler import handlers
from src.query.schema import command, response

router = APIRouter(prefix="/notebooks/{notebook_id}/query", tags=["query"])


@router.post(
    "",
    response_model=response.QueryAnswer,
)
@limiter.limit(QUERY_RATE)
@inject
async def query_notebook(
    request: Request,
    notebook_id: str,
    cmd: command.QueryNotebook,
    handler: handlers.QueryNotebookHandler = Depends(
        Provide[ApplicationContainer.query.handler.query_notebook_handler]
    ),
) -> response.QueryAnswer:
    """Query a notebook with RAG and get an answer with citations."""
    return await handler.handle(notebook_id, cmd)
