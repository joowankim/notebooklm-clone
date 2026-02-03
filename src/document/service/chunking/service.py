"""Chunking service implementation."""

import tiktoken

from src.document.service.chunking.types import ChunkedContent
from src.settings import settings


class ChunkingService:
    """Service for splitting content into chunks with position tracking.

    Uses tiktoken for accurate token counting and splits on sentence/paragraph
    boundaries while preserving exact character positions.
    """

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        encoding_name: str = "cl100k_base",
    ):
        self._chunk_size = chunk_size or settings.chunk_size
        self._chunk_overlap = chunk_overlap or settings.chunk_overlap
        self._encoding = tiktoken.get_encoding(encoding_name)

    def chunk(self, content: str) -> list[ChunkedContent]:
        """Split content into chunks with accurate position tracking.

        CRITICAL: Each chunk's char_start and char_end MUST be accurate.
        Verify with: content[chunk.char_start:chunk.char_end] == chunk.content

        Args:
            content: The text content to chunk.

        Returns:
            List of ChunkedContent with accurate position information.
        """
        if not content.strip():
            return []

        chunks: list[ChunkedContent] = []

        # Split into sentences/paragraphs for natural boundaries
        segments = self._split_into_segments(content)

        current_chunk_text = ""
        current_chunk_start = 0
        chunk_index = 0

        for segment_start, segment_text in segments:
            segment_tokens = len(self._encoding.encode(segment_text))
            current_tokens = len(self._encoding.encode(current_chunk_text))

            # If adding this segment exceeds chunk size, finalize current chunk
            if current_tokens + segment_tokens > self._chunk_size and current_chunk_text:
                chunk = self._create_chunk(
                    content=current_chunk_text,
                    char_start=current_chunk_start,
                    chunk_index=chunk_index,
                )
                chunks.append(chunk)
                chunk_index += 1

                # Calculate overlap start position
                overlap_text, overlap_start = self._calculate_overlap(
                    content, current_chunk_start, segment_start
                )
                current_chunk_text = overlap_text + segment_text
                current_chunk_start = overlap_start
            else:
                if not current_chunk_text:
                    current_chunk_start = segment_start
                current_chunk_text += segment_text

        # Add final chunk
        if current_chunk_text.strip():
            chunk = self._create_chunk(
                content=current_chunk_text,
                char_start=current_chunk_start,
                chunk_index=chunk_index,
            )
            chunks.append(chunk)

        return chunks

    def _split_into_segments(self, content: str) -> list[tuple[int, str]]:
        """Split content into segments at natural boundaries.

        Returns list of (start_position, segment_text) tuples.
        """
        segments: list[tuple[int, str]] = []

        # Split by paragraph boundaries first
        current_pos = 0
        paragraph_delimiters = ["\n\n", "\n"]

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Include the newline in the segment (except for last line)
            if i < len(lines) - 1:
                segment = line + "\n"
            else:
                segment = line

            if segment:  # Skip empty segments
                segments.append((current_pos, segment))

            current_pos += len(line) + (1 if i < len(lines) - 1 else 0)

        return segments

    def _calculate_overlap(
        self, content: str, chunk_start: int, segment_start: int
    ) -> tuple[str, int]:
        """Calculate overlap text and start position for next chunk.

        Returns (overlap_text, overlap_start_position).
        """
        if self._chunk_overlap == 0:
            return "", segment_start

        # Get the text we need to potentially include as overlap
        previous_text = content[chunk_start:segment_start]

        # Count tokens from the end to determine overlap
        tokens = self._encoding.encode(previous_text)

        if len(tokens) <= self._chunk_overlap:
            return previous_text, chunk_start

        # Take only the last overlap_tokens worth of text
        overlap_tokens = tokens[-self._chunk_overlap :]
        overlap_text = self._encoding.decode(overlap_tokens)

        # Find where this overlap text starts in the original
        overlap_start = segment_start - len(overlap_text.encode().decode())

        # Ensure we start at a word boundary
        while overlap_start > chunk_start and content[overlap_start - 1] not in " \n\t":
            overlap_start -= 1

        overlap_text = content[overlap_start:segment_start]
        return overlap_text, overlap_start

    def _create_chunk(
        self, content: str, char_start: int, chunk_index: int
    ) -> ChunkedContent:
        """Create a ChunkedContent with accurate position information."""
        # Strip trailing whitespace but preserve leading
        stripped_content = content.rstrip()
        token_count = len(self._encoding.encode(stripped_content))

        return ChunkedContent(
            content=stripped_content,
            char_start=char_start,
            char_end=char_start + len(stripped_content),
            chunk_index=chunk_index,
            token_count=token_count,
        )

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self._encoding.encode(text))
