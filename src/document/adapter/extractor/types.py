"""Content extraction types."""

import hashlib
from typing import Self

import pydantic


class ExtractedContent(pydantic.BaseModel):
    """Result of content extraction from URL."""

    model_config = pydantic.ConfigDict(frozen=True, extra="forbid")

    url: str
    title: str | None = None
    content: str
    content_hash: str
    word_count: int

    @classmethod
    def create(cls, url: str, title: str | None, content: str) -> Self:
        """Create ExtractedContent with computed fields."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        word_count = len(content.split())

        return cls(
            url=url,
            title=title,
            content=content,
            content_hash=content_hash,
            word_count=word_count,
        )
