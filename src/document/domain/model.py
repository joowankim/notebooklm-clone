"""Document domain entity."""

import datetime
import uuid
from typing import Self

import pydantic

from src import exceptions
from src.common.types import utc_now
from src.document.domain.status import DocumentStatus


class Document(pydantic.BaseModel):
    """Document entity representing a source URL.

    Immutable: all state changes return new instances.
    """

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    id: str
    notebook_id: str
    url: str
    title: str | None = None
    status: DocumentStatus
    error_message: str | None = None
    content_hash: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    @classmethod
    def create(cls, notebook_id: str, url: str, title: str | None = None) -> Self:
        """Factory method to create a new document in PENDING status."""
        now = utc_now()
        return cls(
            id=uuid.uuid4().hex,
            notebook_id=notebook_id,
            url=url,
            title=title,
            status=DocumentStatus.PENDING,
            error_message=None,
            content_hash=None,
            created_at=now,
            updated_at=now,
        )

    def mark_processing(self) -> Self:
        """Mark document as processing."""
        if not self.status.is_processable:
            raise exceptions.InvalidStateError(
                f"Cannot process document in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": DocumentStatus.PROCESSING,
                "updated_at": utc_now(),
            }
        )

    def mark_completed(self, title: str | None = None, content_hash: str | None = None) -> Self:
        """Mark document as completed."""
        if self.status != DocumentStatus.PROCESSING:
            raise exceptions.InvalidStateError(
                f"Cannot complete document in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": DocumentStatus.COMPLETED,
                "title": title if title is not None else self.title,
                "content_hash": content_hash,
                "error_message": None,
                "updated_at": utc_now(),
            }
        )

    def mark_failed(self, error_message: str) -> Self:
        """Mark document as failed."""
        if self.status != DocumentStatus.PROCESSING:
            raise exceptions.InvalidStateError(
                f"Cannot fail document in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": DocumentStatus.FAILED,
                "error_message": error_message,
                "updated_at": utc_now(),
            }
        )

    def retry(self) -> Self:
        """Reset document to PENDING for retry."""
        if not self.status.can_retry:
            raise exceptions.InvalidStateError(
                f"Cannot retry document in status: {self.status}"
            )
        return self.model_copy(
            update={
                "status": DocumentStatus.PENDING,
                "error_message": None,
                "updated_at": utc_now(),
            }
        )
