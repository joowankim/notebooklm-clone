"""Crawl query schemas."""

from src.common import pagination


class ListCrawlJobs(pagination.ListQuery):
    """Query to list crawl jobs for a notebook."""

    notebook_id: str
