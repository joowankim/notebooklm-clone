"""Tests for Notebook repository."""

import pytest

from src.common import ListQuery
from src.notebook.adapter.repository import NotebookRepository
from src.notebook.domain.model import Notebook


@pytest.mark.asyncio
class TestNotebookRepository:
    """Tests for NotebookRepository."""

    async def test_save_and_find_notebook(self, test_session):
        """Test saving and retrieving a notebook."""
        repository = NotebookRepository(test_session)
        notebook = Notebook.create(name="Test Notebook")

        # Save
        saved = await repository.save(notebook)
        assert saved.id == notebook.id

        # Find
        found = await repository.find_by_id(notebook.id)
        assert found is not None
        assert found.name == "Test Notebook"

    async def test_find_nonexistent_notebook(self, test_session):
        """Test finding a notebook that doesn't exist."""
        repository = NotebookRepository(test_session)
        found = await repository.find_by_id("nonexistent")
        assert found is None

    async def test_delete_notebook(self, test_session):
        """Test deleting a notebook."""
        repository = NotebookRepository(test_session)
        notebook = Notebook.create(name="To Delete")
        await repository.save(notebook)

        # Delete
        deleted = await repository.delete(notebook.id)
        assert deleted is True

        # Verify deleted
        found = await repository.find_by_id(notebook.id)
        assert found is None

    async def test_delete_nonexistent_notebook(self, test_session):
        """Test deleting a notebook that doesn't exist."""
        repository = NotebookRepository(test_session)
        deleted = await repository.delete("nonexistent")
        assert deleted is False

    async def test_list_notebooks(self, test_session):
        """Test listing notebooks with pagination."""
        repository = NotebookRepository(test_session)

        # Create notebooks
        for i in range(5):
            await repository.save(Notebook.create(name=f"Notebook {i}"))

        # List with pagination
        result = await repository.list(ListQuery(page=1, size=3))

        assert result.total == 5
        assert len(result.items) == 3
        assert result.page == 1
        assert result.pages == 2

    async def test_list_empty_notebooks(self, test_session):
        """Test listing when no notebooks exist."""
        repository = NotebookRepository(test_session)
        result = await repository.list(ListQuery())

        assert result.total == 0
        assert len(result.items) == 0

    async def test_update_notebook(self, test_session):
        """Test updating a notebook."""
        repository = NotebookRepository(test_session)
        notebook = Notebook.create(name="Original")
        await repository.save(notebook)

        # Update
        updated = notebook.update(name="Updated")
        saved = await repository.save(updated)

        assert saved.name == "Updated"

        # Verify in database
        found = await repository.find_by_id(notebook.id)
        assert found.name == "Updated"
