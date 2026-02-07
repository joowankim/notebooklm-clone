"""Mapper between Notebook entity and ORM schema."""

from src.infrastructure.models import notebook as notebook_schema
from src.notebook.domain import model


class NotebookMapper:
    """Maps between Notebook domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: notebook_schema.NotebookSchema) -> model.Notebook:
        """Convert ORM record to domain entity."""
        return model.Notebook(
            id=record.id,
            name=record.name,
            description=record.description,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(entity: model.Notebook) -> notebook_schema.NotebookSchema:
        """Convert domain entity to ORM record."""
        return notebook_schema.NotebookSchema(
            id=entity.id,
            name=entity.name,
            description=entity.description,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
