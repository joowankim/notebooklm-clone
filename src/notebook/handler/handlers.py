"""Notebook command and query handlers."""

from src import exceptions
from src.common import PaginationSchema
from src.notebook.adapter.repository import NotebookRepository
from src.notebook.domain.model import Notebook
from src.notebook.schema import command, query, response


class CreateNotebookHandler:
    """Handler for creating notebooks."""

    def __init__(self, repository: NotebookRepository):
        self._repository = repository

    async def handle(self, cmd: command.CreateNotebook) -> response.NotebookId:
        """Create a new notebook."""
        notebook = Notebook.create(name=cmd.name, description=cmd.description)
        saved = await self._repository.save(notebook)
        return response.NotebookId(id=saved.id)


class GetNotebookHandler:
    """Handler for getting notebook details."""

    def __init__(self, repository: NotebookRepository):
        self._repository = repository

    async def handle(self, notebook_id: str) -> response.NotebookDetail:
        """Get notebook by ID."""
        notebook = await self._repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")
        return response.NotebookDetail.from_entity(notebook)


class ListNotebooksHandler:
    """Handler for listing notebooks."""

    def __init__(self, repository: NotebookRepository):
        self._repository = repository

    async def handle(
        self, qry: query.ListNotebooks
    ) -> PaginationSchema[response.NotebookDetail]:
        """List notebooks with pagination."""
        result = await self._repository.list(qry)
        return PaginationSchema.create(
            items=[response.NotebookDetail.from_entity(item) for item in result.items],
            total=result.total,
            page=result.page,
            size=result.size,
        )


class UpdateNotebookHandler:
    """Handler for updating notebooks."""

    def __init__(self, repository: NotebookRepository):
        self._repository = repository

    async def handle(
        self, notebook_id: str, cmd: command.UpdateNotebook
    ) -> response.NotebookDetail:
        """Update an existing notebook."""
        notebook = await self._repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")

        updated = notebook.update(name=cmd.name, description=cmd.description)
        saved = await self._repository.save(updated)
        return response.NotebookDetail.from_entity(saved)


class DeleteNotebookHandler:
    """Handler for deleting notebooks."""

    def __init__(self, repository: NotebookRepository):
        self._repository = repository

    async def handle(self, notebook_id: str) -> None:
        """Delete notebook by ID."""
        deleted = await self._repository.delete(notebook_id)
        if not deleted:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")
