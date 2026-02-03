"""Tests for document repository."""

import pytest

from src.common import ListQuery
from src.document.adapter.repository import DocumentRepository
from src.document.domain.model import Document
from src.document.domain.status import DocumentStatus
from src.notebook.adapter.repository import NotebookRepository
from src.notebook.domain.model import Notebook


class TestDocumentRepository:
    """Tests for DocumentRepository."""

    @pytest.fixture
    async def notebook(self, test_session) -> Notebook:
        """Create a test notebook."""
        notebook = Notebook.create(
            name="Test Notebook",
            description="For document tests",
        )
        repo = NotebookRepository(test_session)
        await repo.save(notebook)
        return notebook

    @pytest.fixture
    def repository(self, test_session) -> DocumentRepository:
        """Create repository instance."""
        return DocumentRepository(test_session)

    @pytest.mark.asyncio
    async def test_save_and_find_document(self, repository, notebook):
        """Test saving and finding a document."""
        document = Document.create(
            notebook_id=notebook.id,
            url="https://example.com/test",
        )

        await repository.save(document)
        found = await repository.find_by_id(document.id)

        assert found is not None
        assert found.id == document.id
        assert found.url == "https://example.com/test"
        assert found.status == DocumentStatus.PENDING

    @pytest.mark.asyncio
    async def test_find_nonexistent_document(self, repository):
        """Test finding non-existent document returns None."""
        found = await repository.find_by_id("nonexistent")
        assert found is None

    @pytest.mark.asyncio
    async def test_find_by_notebook_and_url(self, repository, notebook):
        """Test finding document by notebook ID and URL."""
        document = Document.create(
            notebook_id=notebook.id,
            url="https://example.com/unique",
        )
        await repository.save(document)

        found = await repository.find_by_notebook_and_url(
            notebook_id=notebook.id,
            url="https://example.com/unique",
        )

        assert found is not None
        assert found.id == document.id

    @pytest.mark.asyncio
    async def test_find_by_notebook_and_url_not_found(self, repository, notebook):
        """Test finding non-existent URL returns None."""
        found = await repository.find_by_notebook_and_url(
            notebook_id=notebook.id,
            url="https://nonexistent.com",
        )
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_document(self, repository, notebook):
        """Test deleting a document."""
        document = Document.create(
            notebook_id=notebook.id,
            url="https://example.com/delete",
        )
        await repository.save(document)

        result = await repository.delete(document.id)
        assert result is True

        found = await repository.find_by_id(document.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_document(self, repository):
        """Test deleting non-existent document returns False."""
        result = await repository.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_documents_by_notebook(self, repository, notebook):
        """Test listing documents by notebook."""
        # Create multiple documents
        for i in range(3):
            document = Document.create(
                notebook_id=notebook.id,
                url=f"https://example.com/doc{i}",
            )
            await repository.save(document)

        result = await repository.list_by_notebook(
            notebook_id=notebook.id,
            query=ListQuery(page=1, size=10),
        )

        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_list_documents_pagination(self, repository, notebook):
        """Test document list pagination."""
        # Create 5 documents
        for i in range(5):
            document = Document.create(
                notebook_id=notebook.id,
                url=f"https://example.com/page{i}",
            )
            await repository.save(document)

        result = await repository.list_by_notebook(
            notebook_id=notebook.id,
            query=ListQuery(page=1, size=2),
        )

        assert result.total == 5
        assert len(result.items) == 2
        assert result.pages == 3

    @pytest.mark.asyncio
    async def test_update_document_status(self, repository, notebook):
        """Test updating document status."""
        document = Document.create(
            notebook_id=notebook.id,
            url="https://example.com/update",
        )
        await repository.save(document)

        # Update to processing
        updated = document.mark_processing()
        await repository.save(updated)

        found = await repository.find_by_id(document.id)
        assert found is not None
        assert found.status == DocumentStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_update_document_with_title(self, repository, notebook):
        """Test updating document with title."""
        document = Document.create(
            notebook_id=notebook.id,
            url="https://example.com/titled",
        )
        await repository.save(document)

        # Start processing then mark completed with title
        processing = document.mark_processing()
        await repository.save(processing)

        completed = processing.mark_completed(
            title="Test Title",
            content_hash="abc123",
        )
        await repository.save(completed)

        found = await repository.find_by_id(document.id)
        assert found is not None
        assert found.title == "Test Title"
        assert found.content_hash == "abc123"
