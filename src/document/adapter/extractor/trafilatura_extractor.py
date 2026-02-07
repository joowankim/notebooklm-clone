"""Trafilatura content extractor."""

import httpx
import trafilatura

from src import exceptions
from src.document.adapter.extractor import port as extractor_port
from src.document.adapter.extractor import types as extractor_types


class TrafilaturaExtractor(extractor_port.ContentExtractorPort):
    """Content extractor using Trafilatura library.

    Trafilatura is a Python library for web scraping and text extraction.
    It's used as a fallback when Jina Reader is unavailable.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    async def extract(self, url: str) -> extractor_types.ExtractedContent:
        """Extract content from URL using Trafilatura."""
        try:
            # Fetch the HTML content
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (compatible; NotebookLM-Clone/1.0; "
                            "+https://github.com/example/ntlm-clone)"
                        )
                    },
                )
                response.raise_for_status()
                html_content = response.text

        except httpx.TimeoutException as exc:
            raise exceptions.ExternalServiceError(f"Request timeout for URL: {url}") from exc
        except httpx.HTTPStatusError as exc:
            raise exceptions.ExternalServiceError(
                f"HTTP error {exc.response.status_code} for URL: {url}"
            ) from exc
        except httpx.RequestError as exc:
            raise exceptions.ExternalServiceError(
                f"Request error for URL: {url}: {exc}"
            ) from exc

        # Extract content using trafilatura
        content = trafilatura.extract(
            html_content,
            include_links=False,
            include_images=False,
            include_tables=True,
            output_format="txt",
        )

        if content is None:
            raise exceptions.ExternalServiceError(
                f"Could not extract content from URL: {url}"
            )

        # Extract metadata
        metadata = trafilatura.extract_metadata(html_content)
        title = metadata.title if metadata else None

        return extractor_types.ExtractedContent.create(
            url=url,
            title=title,
            content=content,
        )

    def supports(self, url: str) -> bool:
        """Check if this extractor supports the URL."""
        # Trafilatura supports HTTP/HTTPS URLs
        return url.startswith(("http://", "https://"))
