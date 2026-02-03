"""Jina Reader content extractor."""

import httpx

from src import exceptions
from src.document.adapter.extractor.port import ContentExtractorPort
from src.document.adapter.extractor.types import ExtractedContent
from src.settings import settings


class JinaReaderExtractor(ContentExtractorPort):
    """Content extractor using Jina Reader API.

    Jina Reader (r.jina.ai) converts URLs to clean markdown content.
    """

    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        self._api_key = api_key or settings.jina_api_key
        self._timeout = timeout
        self._base_url = "https://r.jina.ai"

    async def extract(self, url: str) -> ExtractedContent:
        """Extract content from URL using Jina Reader."""
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # Jina Reader URL format: https://r.jina.ai/<url>
        reader_url = f"{self._base_url}/{url}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(reader_url, headers=headers)
                response.raise_for_status()

                content = response.text

                # Try to extract title from first markdown heading
                title = self._extract_title(content)

                return ExtractedContent.create(
                    url=url,
                    title=title,
                    content=content,
                )

        except httpx.TimeoutException:
            raise exceptions.ExternalServiceError(
                f"Jina Reader timeout for URL: {url}"
            )
        except httpx.HTTPStatusError as e:
            raise exceptions.ExternalServiceError(
                f"Jina Reader HTTP error {e.response.status_code} for URL: {url}"
            )
        except httpx.RequestError as e:
            raise exceptions.ExternalServiceError(
                f"Jina Reader request error for URL: {url}: {e}"
            )

    def supports(self, url: str) -> bool:
        """Check if this extractor supports the URL."""
        # Jina Reader supports most HTTP/HTTPS URLs
        return url.startswith(("http://", "https://"))

    def _extract_title(self, content: str) -> str | None:
        """Extract title from first markdown heading."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return None
