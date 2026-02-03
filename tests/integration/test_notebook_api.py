"""Integration tests for notebook API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.database import Base
from src.dependency.container import ApplicationContainer
from src.main import app, container


@pytest.fixture
def test_app(test_engine):
    """Create test app with overridden database session."""

    async def override_session():
        """Create session factory for tests."""
        session_factory = async_sessionmaker(
            test_engine,
            expire_on_commit=False,
        )
        async with session_factory() as session:
            yield session
            await session.commit()

    # We can't directly override async dependencies in sync TestClient
    # So we'll use the standard app for now
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestNotebookAPI:
    """Integration tests for notebook endpoints."""

    @pytest.mark.skip(reason="Requires PostgreSQL with pgvector for full integration")
    def test_create_notebook(self, client):
        """Test creating a notebook via API."""
        response = client.post(
            "/api/v1/notebooks",
            json={"name": "Test Notebook", "description": "A test notebook"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert len(data["id"]) == 32

    @pytest.mark.skip(reason="Requires PostgreSQL with pgvector for full integration")
    def test_get_notebook(self, client):
        """Test getting a notebook via API."""
        # Create notebook first
        create_response = client.post(
            "/api/v1/notebooks",
            json={"name": "Test Notebook"},
        )
        notebook_id = create_response.json()["id"]

        # Get notebook
        response = client.get(f"/api/v1/notebooks/{notebook_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == notebook_id
        assert data["name"] == "Test Notebook"

    @pytest.mark.skip(reason="Requires PostgreSQL with pgvector for full integration")
    def test_list_notebooks(self, client):
        """Test listing notebooks via API."""
        # Create some notebooks
        for i in range(3):
            client.post(
                "/api/v1/notebooks",
                json={"name": f"Notebook {i}"},
            )

        # List notebooks
        response = client.get("/api/v1/notebooks")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3

    @pytest.mark.skip(reason="Requires PostgreSQL with pgvector for full integration")
    def test_update_notebook(self, client):
        """Test updating a notebook via API."""
        # Create notebook
        create_response = client.post(
            "/api/v1/notebooks",
            json={"name": "Original Name"},
        )
        notebook_id = create_response.json()["id"]

        # Update notebook
        response = client.patch(
            f"/api/v1/notebooks/{notebook_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.skip(reason="Requires PostgreSQL with pgvector for full integration")
    def test_delete_notebook(self, client):
        """Test deleting a notebook via API."""
        # Create notebook
        create_response = client.post(
            "/api/v1/notebooks",
            json={"name": "To Delete"},
        )
        notebook_id = create_response.json()["id"]

        # Delete notebook
        response = client.delete(f"/api/v1/notebooks/{notebook_id}")
        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/notebooks/{notebook_id}")
        assert get_response.status_code == 404

    def test_get_nonexistent_notebook(self, client):
        """Test getting a non-existent notebook returns 404."""
        response = client.get("/api/v1/notebooks/nonexistent123456789012")
        assert response.status_code == 404

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
