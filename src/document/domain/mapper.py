"""Mapper between Document entity and ORM schema."""

from src.document.domain import model
from src.document.domain.status import DocumentStatus
from src.infrastructure.models import document as document_schema


class DocumentMapper:
    """Maps between Document domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: document_schema.DocumentSchema) -> model.Document:
        """Convert ORM record to domain entity."""
        return model.Document(
            id=record.id,
            notebook_id=record.notebook_id,
            url=record.url,
            title=record.title,
            status=DocumentStatus(record.status),
            error_message=record.error_message,
            content_hash=record.content_hash,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def to_record(entity: model.Document) -> document_schema.DocumentSchema:
        """Convert domain entity to ORM record."""
        return document_schema.DocumentSchema(
            id=entity.id,
            notebook_id=entity.notebook_id,
            url=entity.url,
            title=entity.title,
            status=entity.status.value,
            error_message=entity.error_message,
            content_hash=entity.content_hash,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
