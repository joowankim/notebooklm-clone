"""Query response schemas (output DTOs)."""

import pydantic


class Citation(pydantic.BaseModel):
    """A citation referencing source material."""

    citation_index: int  # [1], [2], etc.
    document_id: str
    chunk_id: str
    document_title: str | None
    document_url: str
    char_start: int
    char_end: int
    snippet: str  # Snippet of the cited text


class QueryAnswer(pydantic.BaseModel):
    """Response to a RAG query with citations."""

    answer: str
    citations: list[Citation]
    sources_used: int
