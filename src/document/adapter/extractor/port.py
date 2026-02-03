"""Content extractor port (interface)."""

import abc

from src.document.adapter.extractor.types import ExtractedContent


class ContentExtractorPort(abc.ABC):
    """Abstract interface for content extraction."""

    @abc.abstractmethod
    async def extract(self, url: str) -> ExtractedContent:
        """Extract content from a URL.

        Args:
            url: The URL to extract content from.

        Returns:
            ExtractedContent with the extracted text.

        Raises:
            ExternalServiceError: If extraction fails.
        """
        ...

    @abc.abstractmethod
    def supports(self, url: str) -> bool:
        """Check if this extractor supports the given URL.

        Args:
            url: The URL to check.

        Returns:
            True if this extractor can handle the URL.
        """
        ...
