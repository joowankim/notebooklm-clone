"""Tests for chunking service."""

import pytest

from src.document.service.chunking.service import ChunkingService


class TestChunkingService:
    """Tests for ChunkingService."""

    def test_chunk_empty_content(self):
        """Test chunking empty content."""
        service = ChunkingService()
        chunks = service.chunk("")
        assert chunks == []

    def test_chunk_whitespace_content(self):
        """Test chunking whitespace-only content."""
        service = ChunkingService()
        chunks = service.chunk("   \n\n   ")
        assert chunks == []

    def test_chunk_small_content(self):
        """Test chunking content smaller than chunk size."""
        service = ChunkingService(chunk_size=1000)
        content = "This is a small piece of content."
        chunks = service.chunk(content)

        assert len(chunks) == 1
        assert chunks[0].content == content
        assert chunks[0].char_start == 0
        assert chunks[0].char_end == len(content)

    def test_chunk_position_accuracy(self):
        """Test that char_start/char_end accurately map to content."""
        service = ChunkingService(chunk_size=50, chunk_overlap=10)
        content = """This is the first paragraph with some content.
This is the second paragraph with different content.
This is the third paragraph with even more content.
This is the fourth paragraph to ensure multiple chunks."""

        chunks = service.chunk(content)

        # Verify each chunk's position accuracy
        for chunk in chunks:
            extracted = content[chunk.char_start : chunk.char_end]
            assert extracted == chunk.content, (
                f"Position mismatch for chunk {chunk.chunk_index}: "
                f"extracted={repr(extracted)}, content={repr(chunk.content)}"
            )

    def test_chunk_index_sequential(self):
        """Test that chunk indices are sequential."""
        service = ChunkingService(chunk_size=50, chunk_overlap=10)
        content = "Word " * 100  # Long content

        chunks = service.chunk(content)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_chunk_token_count(self):
        """Test that token count is calculated."""
        service = ChunkingService(chunk_size=1000)
        content = "Hello world, this is a test."
        chunks = service.chunk(content)

        assert len(chunks) == 1
        assert chunks[0].token_count > 0

    def test_count_tokens(self):
        """Test token counting."""
        service = ChunkingService()
        count = service.count_tokens("Hello world")
        assert count > 0

    def test_verify_position_method(self):
        """Test ChunkedContent.verify_position method."""
        service = ChunkingService(chunk_size=100)
        content = "This is test content for verification."
        chunks = service.chunk(content)

        for chunk in chunks:
            assert chunk.verify_position(content) is True
