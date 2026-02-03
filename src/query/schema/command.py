"""Query command schemas (input DTOs)."""

import pydantic


class QueryNotebook(pydantic.BaseModel):
    """Command to query a notebook with RAG."""

    model_config = pydantic.ConfigDict(extra="forbid")

    question: str = pydantic.Field(..., min_length=1, max_length=2000)
    max_sources: int = pydantic.Field(default=5, ge=1, le=20)
