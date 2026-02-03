"""Tests for chunk domain model."""

import datetime
import uuid

import pytest

from src.chunk.domain.model import Chunk


class TestChunkModel:
    """Tests for Chunk entity."""

    def test_create_chunk(self):
        """Test creating a chunk."""
        now = datetime.datetime.now(datetime.timezone.utc)
        chunk = Chunk(
            id=uuid.uuid4().hex,
            document_id="doc123",
            content="This is chunk content.",
            char_start=0,
            char_end=22,
            chunk_index=0,
            token_count=5,
            embedding=None,
            created_at=now,
        )

        assert chunk.document_id == "doc123"
        assert chunk.content == "This is chunk content."
        assert chunk.char_start == 0
        assert chunk.char_end == 22
        assert chunk.chunk_index == 0
        assert chunk.token_count == 5
        assert chunk.embedding is None

    def test_create_chunk_with_embedding(self):
        """Test creating a chunk with embedding."""
        now = datetime.datetime.now(datetime.timezone.utc)
        embedding = [0.1] * 1536  # OpenAI embedding dimension

        chunk = Chunk(
            id=uuid.uuid4().hex,
            document_id="doc123",
            content="Content",
            char_start=0,
            char_end=7,
            chunk_index=0,
            token_count=1,
            embedding=embedding,
            created_at=now,
        )

        assert chunk.embedding is not None
        assert len(chunk.embedding) == 1536

    def test_chunk_create_factory(self):
        """Test Chunk.create factory method."""
        chunk = Chunk.create(
            document_id="doc123",
            content="Test content",
            char_start=10,
            char_end=22,
            chunk_index=1,
            token_count=3,
        )

        assert chunk.document_id == "doc123"
        assert chunk.content == "Test content"
        assert chunk.char_start == 10
        assert chunk.char_end == 22
        assert chunk.chunk_index == 1
        assert chunk.token_count == 3
        assert len(chunk.id) == 32  # UUID hex

    def test_chunk_with_embedding(self):
        """Test adding embedding to a chunk."""
        chunk = Chunk.create(
            document_id="doc123",
            content="Content",
            char_start=0,
            char_end=7,
            chunk_index=0,
            token_count=1,
        )

        assert chunk.embedding is None

        embedding = [0.2] * 1536
        updated = chunk.with_embedding(embedding)

        # Original should be unchanged (immutability)
        assert chunk.embedding is None
        # Updated should have embedding
        assert updated.embedding is not None
        assert len(updated.embedding) == 1536

    def test_chunk_immutability(self):
        """Test that chunk is immutable."""
        chunk = Chunk.create(
            document_id="doc123",
            content="Content",
            char_start=0,
            char_end=7,
            chunk_index=0,
            token_count=1,
        )

        with pytest.raises(Exception):  # Should raise on mutation
            chunk.content = "New content"

    def test_chunk_position_consistency(self):
        """Test that char_start and char_end correctly bound the content."""
        content = "This is a test document for chunking."
        char_start = 0
        char_end = len(content)

        chunk = Chunk.create(
            document_id="doc123",
            content=content,
            char_start=char_start,
            char_end=char_end,
            chunk_index=0,
            token_count=8,
        )

        # The content length should match the position range
        assert chunk.char_end - chunk.char_start == len(chunk.content)
