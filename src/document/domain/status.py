"""Document status enum with state machine properties."""

import enum


class DocumentStatus(enum.StrEnum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_processable(self) -> bool:
        """Check if document can be processed."""
        return self == DocumentStatus.PENDING

    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (cannot change)."""
        return self in (DocumentStatus.COMPLETED, DocumentStatus.FAILED)

    @property
    def can_retry(self) -> bool:
        """Check if document processing can be retried."""
        return self == DocumentStatus.FAILED
