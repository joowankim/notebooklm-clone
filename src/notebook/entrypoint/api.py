"""Notebook REST API router."""

import http

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from src.common import PaginationSchema
from src.dependency.container import ApplicationContainer
from src.notebook.handler import handlers
from src.notebook.schema import command, query, response

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.post(
    "",
    response_model=response.NotebookId,
    status_code=http.HTTPStatus.CREATED,
)
@inject
async def create_notebook(
    cmd: command.CreateNotebook,
    handler: handlers.CreateNotebookHandler = Depends(
        Provide[ApplicationContainer.notebook.handler.create_notebook_handler]
    ),
) -> response.NotebookId:
    """Create a new notebook."""
    return await handler.handle(cmd)


@router.get(
    "",
    response_model=PaginationSchema[response.NotebookDetail],
)
@inject
async def list_notebooks(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    handler: handlers.ListNotebooksHandler = Depends(
        Provide[ApplicationContainer.notebook.handler.list_notebooks_handler]
    ),
) -> PaginationSchema[response.NotebookDetail]:
    """List notebooks with pagination."""
    qry = query.ListNotebooks(page=page, size=size)
    return await handler.handle(qry)


@router.get(
    "/{notebook_id}",
    response_model=response.NotebookDetail,
)
@inject
async def get_notebook(
    notebook_id: str,
    handler: handlers.GetNotebookHandler = Depends(
        Provide[ApplicationContainer.notebook.handler.get_notebook_handler]
    ),
) -> response.NotebookDetail:
    """Get notebook by ID."""
    return await handler.handle(notebook_id)


@router.patch(
    "/{notebook_id}",
    response_model=response.NotebookDetail,
)
@inject
async def update_notebook(
    notebook_id: str,
    cmd: command.UpdateNotebook,
    handler: handlers.UpdateNotebookHandler = Depends(
        Provide[ApplicationContainer.notebook.handler.update_notebook_handler]
    ),
) -> response.NotebookDetail:
    """Update an existing notebook."""
    return await handler.handle(notebook_id, cmd)


@router.delete(
    "/{notebook_id}",
    status_code=http.HTTPStatus.NO_CONTENT,
)
@inject
async def delete_notebook(
    notebook_id: str,
    handler: handlers.DeleteNotebookHandler = Depends(
        Provide[ApplicationContainer.notebook.handler.delete_notebook_handler]
    ),
) -> None:
    """Delete notebook by ID."""
    await handler.handle(notebook_id)
