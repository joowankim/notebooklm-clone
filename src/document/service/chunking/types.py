"""Chunking types."""

import pydantic


class ChunkedContent(pydantic.BaseModel):
    """A chunk of content with position information.

    CRITICAL: char_start and char_end must be accurate for citation navigation.
    The original content[char_start:char_end] MUST equal this chunk's content.
    """

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    content: str
    char_start: int
    char_end: int
    chunk_index: int
    token_count: int

    def verify_position(self, original_content: str) -> bool:
        """Verify that char_start/char_end correctly maps to original content."""
        extracted = original_content[self.char_start : self.char_end]
        return extracted == self.content
