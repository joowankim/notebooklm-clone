"""Composite content extractor with fallback."""

import logging

from src import exceptions
from src.document.adapter.extractor.jina import JinaReaderExtractor
from src.document.adapter.extractor.port import ContentExtractorPort
from src.document.adapter.extractor.trafilatura_extractor import TrafilaturaExtractor
from src.document.adapter.extractor.types import ExtractedContent

logger = logging.getLogger(__name__)


class CompositeExtractor(ContentExtractorPort):
    """Composite extractor that tries multiple extractors with fallback.

    Order of preference:
    1. Jina Reader (if API key configured)
    2. Trafilatura (local fallback)
    """

    def __init__(
        self,
        jina_api_key: str | None = None,
        timeout: float = 30.0,
    ):
        self._extractors: list[ContentExtractorPort] = []

        # Add Jina Reader if API key is available
        if jina_api_key:
            self._extractors.append(
                JinaReaderExtractor(api_key=jina_api_key, timeout=timeout)
            )

        # Always add Trafilatura as fallback
        self._extractors.append(TrafilaturaExtractor(timeout=timeout))

    async def extract(self, url: str) -> ExtractedContent:
        """Extract content using available extractors with fallback."""
        errors: list[str] = []

        for extractor in self._extractors:
            if not extractor.supports(url):
                continue

            try:
                result = await extractor.extract(url)
                logger.info(
                    f"Successfully extracted content from {url} "
                    f"using {extractor.__class__.__name__}"
                )
                return result
            except exceptions.ExternalServiceError as e:
                logger.warning(
                    f"Extractor {extractor.__class__.__name__} failed for {url}: {e}"
                )
                errors.append(f"{extractor.__class__.__name__}: {e.message}")
                continue

        raise exceptions.ExternalServiceError(
            f"All extractors failed for URL: {url}. Errors: {'; '.join(errors)}"
        )

    def supports(self, url: str) -> bool:
        """Check if any extractor supports the URL."""
        return any(extractor.supports(url) for extractor in self._extractors)
