"""Conversation query schemas."""

from src.common import ListQuery


class ListConversations(ListQuery):
    """Query to list conversations for a notebook."""

    notebook_id: str
