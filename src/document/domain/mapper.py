"""Mapper between Document entity and ORM schema."""

from src.document.domain.model import Document
from src.document.domain.status import DocumentStatus
from src.infrastructure.models.document import DocumentSchema


class DocumentMapper:
    """Maps between Document domain entity and ORM schema."""

    @staticmethod
    def to_entity(record: DocumentSchema) -> Document:
        """Convert ORM record to domain entity."""
        return Document(
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
    def to_record(entity: Document) -> DocumentSchema:
        """Convert domain entity to ORM record."""
        return DocumentSchema(
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
