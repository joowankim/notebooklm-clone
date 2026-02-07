"""Notebook query schemas."""

from src.common import pagination


class ListNotebooks(pagination.ListQuery):
    """Query to list notebooks with pagination."""

    pass
