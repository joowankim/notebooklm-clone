"""Tests for Notebook domain model."""

import pytest

from src.notebook.domain.model import Notebook


class TestNotebookModel:
    """Tests for Notebook entity."""

    def test_create_notebook(self):
        """Test notebook creation with factory method."""
        notebook = Notebook.create(name="Test Notebook", description="A test")

        assert notebook.id is not None
        assert len(notebook.id) == 32  # UUID hex
        assert notebook.name == "Test Notebook"
        assert notebook.description == "A test"
        assert notebook.created_at is not None
        assert notebook.updated_at is not None

    def test_create_notebook_without_description(self):
        """Test notebook creation without description."""
        notebook = Notebook.create(name="Test")

        assert notebook.description is None

    def test_update_notebook_name(self):
        """Test notebook update returns new instance."""
        original = Notebook.create(name="Original")
        updated = original.update(name="Updated")

        # Original unchanged (immutability)
        assert original.name == "Original"

        # Updated has new name
        assert updated.name == "Updated"
        assert updated.id == original.id
        assert updated.updated_at >= original.updated_at

    def test_update_notebook_description(self):
        """Test notebook description update."""
        original = Notebook.create(name="Test", description="Old")
        updated = original.update(description="New")

        assert updated.description == "New"
        assert updated.name == "Test"

    def test_notebook_immutability(self):
        """Test that notebook is immutable."""
        notebook = Notebook.create(name="Test")

        with pytest.raises(Exception):  # ValidationError for frozen model
            notebook.name = "Modified"
