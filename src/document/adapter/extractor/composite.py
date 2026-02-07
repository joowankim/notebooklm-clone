"""Composite content extractor with fallback."""

import logging

from src import exceptions
from src.document.adapter.extractor import jina as jina_module
from src.document.adapter.extractor import port as extractor_port
from src.document.adapter.extractor import trafilatura_extractor as trafilatura_module
from src.document.adapter.extractor import types as extractor_types

logger = logging.getLogger(__name__)


class CompositeExtractor(extractor_port.ContentExtractorPort):
    """Composite extractor that tries multiple extractors with fallback.

    Order of preference:
    1. Jina Reader (if API key configured)
    2. Trafilatura (local fallback)
    """

    def __init__(
        self,
        jina_api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._extractors: list[extractor_port.ContentExtractorPort] = []

        # Add Jina Reader if API key is available
        if jina_api_key:
            self._extractors.append(
                jina_module.JinaReaderExtractor(api_key=jina_api_key, timeout=timeout)
            )

        # Always add Trafilatura as fallback
        self._extractors.append(trafilatura_module.TrafilaturaExtractor(timeout=timeout))

    async def extract(self, url: str) -> extractor_types.ExtractedContent:
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
