"""Query REST API router."""

import fastapi
from dependency_injector.wiring import Provide, inject

from src.common import rate_limit
from src.dependency import container as container_module
from src.query.handler import handlers
from src.query.schema import command, response

router = fastapi.APIRouter(prefix="/notebooks/{notebook_id}/query", tags=["query"])


@router.post(
    "",
    response_model=response.QueryAnswer,
)
@rate_limit.limiter.limit(rate_limit.QUERY_RATE)
@inject
async def query_notebook(
    request: fastapi.Request,
    notebook_id: str,
    cmd: command.QueryNotebook,
    handler: handlers.QueryNotebookHandler = fastapi.Depends(
        Provide[container_module.ApplicationContainer.query.handler.query_notebook_handler]
    ),
) -> response.QueryAnswer:
    """Query a notebook with RAG and get an answer with citations."""
    return await handler.handle(notebook_id, cmd)
