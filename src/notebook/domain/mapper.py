"""Mapper between Notebook entity and ORM schema."""

from src.infrastructure.models.notebook import NotebookSchema
from src.notebook.domain.model import Notebook


class NotebookMapper:
    """Maps between Notebook domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: NotebookSchema) -> Notebook:
        """Convert ORM record to domain entity."""
        return Notebook(
            id=record.id,
            name=record.name,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(entity: Notebook) -> NotebookSchema:
        """Convert domain entity to ORM record."""
        return NotebookSchema(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
