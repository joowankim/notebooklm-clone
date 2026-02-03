"""Document command and query handlers."""

from src import exceptions
from src.common import PaginationSchema
from src.document.adapter.repository import DocumentRepository
from src.document.domain.model import Document
from src.document.schema import command, query, response
from src.document.service.ingestion_pipeline import BackgroundIngestionService
from src.notebook.adapter.repository import NotebookRepository


class AddSourceHandler:
    """Handler for adding source URLs to notebooks."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        notebook_repository: NotebookRepository,
        background_ingestion: BackgroundIngestionService,
    ):
        self._document_repository = document_repository
        self._notebook_repository = notebook_repository
        self._background_ingestion = background_ingestion

    async def handle(
        self, notebook_id: str, cmd: command.AddSource
    ) -> response.DocumentId:
        """Add a source URL to a notebook and trigger async ingestion."""
        # Verify notebook exists
        notebook = await self._notebook_repository.find_by_id(notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {notebook_id}")

        # Check for duplicate URL
        url_str = str(cmd.url)
        existing = await self._document_repository.find_by_notebook_and_url(
            notebook_id, url_str
        )
        if existing is not None:
            raise exceptions.ValidationError(
                f"Source URL already exists in notebook: {url_str}"
            )

        # Create document
        document = Document.create(
            notebook_id=notebook_id,
            url=url_str,
            title=cmd.title,
        )
        saved = await self._document_repository.save(document)

        # Trigger async ingestion (fire and forget)
        self._background_ingestion.trigger_ingestion(saved)

        return response.DocumentId(id=saved.id)


class GetDocumentHandler:
    """Handler for getting document details."""

    def __init__(self, repository: DocumentRepository):
        self._repository = repository

    async def handle(self, document_id: str) -> response.DocumentDetail:
        """Get document by ID."""
        document = await self._repository.find_by_id(document_id)
        if document is None:
            raise exceptions.NotFoundError(f"Document not found: {document_id}")
        return response.DocumentDetail.from_entity(document)


class ListSourcesHandler:
    """Handler for listing sources in a notebook."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        notebook_repository: NotebookRepository,
    ):
        self._document_repository = document_repository
        self._notebook_repository = notebook_repository

    async def handle(
        self, qry: query.ListSources
    ) -> PaginationSchema[response.DocumentDetail]:
        """List sources for a notebook with pagination."""
        # Verify notebook exists
        notebook = await self._notebook_repository.find_by_id(qry.notebook_id)
        if notebook is None:
            raise exceptions.NotFoundError(f"Notebook not found: {qry.notebook_id}")

        result = await self._document_repository.list_by_notebook(qry.notebook_id, qry)
        return PaginationSchema.create(
            items=[response.DocumentDetail.from_entity(item) for item in result.items],
            total=result.total,
            page=result.page,
            size=result.size,
        )
