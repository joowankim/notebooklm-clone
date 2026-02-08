"""Crawl command schemas (input DTOs)."""

import pydantic

from src.crawl.domain.model import DEFAULT_MAX_DEPTH, DEFAULT_MAX_PAGES


class StartCrawl(pydantic.BaseModel):
    """Command to start crawling from a seed URL."""

    model_config = pydantic.ConfigDict(extra="forbid")

    url: pydantic.HttpUrl
    max_depth: int = pydantic.Field(default=DEFAULT_MAX_DEPTH, ge=1, le=10)
    max_pages: int = pydantic.Field(default=DEFAULT_MAX_PAGES, ge=1, le=500)
    url_include_pattern: str | None = None
    url_exclude_pattern: str | None = None
