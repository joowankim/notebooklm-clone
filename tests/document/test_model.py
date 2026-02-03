"""Tests for Document domain model."""

import pytest

from src import exceptions
from src.document.domain.model import Document
from src.document.domain.status import DocumentStatus


class TestDocumentModel:
    """Tests for Document entity."""

    def test_create_document(self):
        """Test document creation with factory method."""
        document = Document.create(
            notebook_id="nb123",
            url="https://example.com",
            title="Example",
        )

        assert document.id is not None
        assert document.notebook_id == "nb123"
        assert document.url == "https://example.com"
        assert document.title == "Example"
        assert document.status == DocumentStatus.PENDING

    def test_document_state_machine_happy_path(self):
        """Test valid state transitions."""
        document = Document.create(notebook_id="nb123", url="https://example.com")

        # PENDING -> PROCESSING
        processing = document.mark_processing()
        assert processing.status == DocumentStatus.PROCESSING

        # PROCESSING -> COMPLETED
        completed = processing.mark_completed(title="Extracted Title")
        assert completed.status == DocumentStatus.COMPLETED
        assert completed.title == "Extracted Title"

    def test_document_failed_state(self):
        """Test failed state transition."""
        document = Document.create(notebook_id="nb123", url="https://example.com")
        processing = document.mark_processing()

        # PROCESSING -> FAILED
        failed = processing.mark_failed("Network error")
        assert failed.status == DocumentStatus.FAILED
        assert failed.error_message == "Network error"

    def test_retry_from_failed(self):
        """Test retry resets to PENDING."""
        document = Document.create(notebook_id="nb123", url="https://example.com")
        failed = document.mark_processing().mark_failed("Error")

        # FAILED -> PENDING (retry)
        retried = failed.retry()
        assert retried.status == DocumentStatus.PENDING
        assert retried.error_message is None

    def test_invalid_state_transition_process_completed(self):
        """Test cannot process a completed document."""
        document = Document.create(notebook_id="nb123", url="https://example.com")
        completed = document.mark_processing().mark_completed()

        with pytest.raises(exceptions.InvalidStateError):
            completed.mark_processing()

    def test_invalid_state_transition_complete_pending(self):
        """Test cannot complete a pending document."""
        document = Document.create(notebook_id="nb123", url="https://example.com")

        with pytest.raises(exceptions.InvalidStateError):
            document.mark_completed()

    def test_invalid_retry_from_completed(self):
        """Test cannot retry a completed document."""
        document = Document.create(notebook_id="nb123", url="https://example.com")
        completed = document.mark_processing().mark_completed()

        with pytest.raises(exceptions.InvalidStateError):
            completed.retry()


class TestDocumentStatus:
    """Tests for DocumentStatus enum."""

    def test_is_processable(self):
        """Test is_processable property."""
        assert DocumentStatus.PENDING.is_processable is True
        assert DocumentStatus.PROCESSING.is_processable is False
        assert DocumentStatus.COMPLETED.is_processable is False
        assert DocumentStatus.FAILED.is_processable is False

    def test_is_terminal(self):
        """Test is_terminal property."""
        assert DocumentStatus.PENDING.is_terminal is False
        assert DocumentStatus.PROCESSING.is_terminal is False
        assert DocumentStatus.COMPLETED.is_terminal is True
        assert DocumentStatus.FAILED.is_terminal is True

    def test_can_retry(self):
        """Test can_retry property."""
        assert DocumentStatus.PENDING.can_retry is False
        assert DocumentStatus.PROCESSING.can_retry is False
        assert DocumentStatus.COMPLETED.can_retry is False
        assert DocumentStatus.FAILED.can_retry is True
