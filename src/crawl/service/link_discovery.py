"""Link discovery service for extracting internal links from web pages."""

import logging
import re
import urllib.parse

import httpx
import lxml.html

from src.crawl.domain import model

logger = logging.getLogger(__name__)

NON_HTTP_SCHEMES = frozenset({"mailto", "javascript", "tel", "ftp", "data"})
HTTP_TIMEOUT_SECONDS = 30


class LinkDiscoveryService:
    """Fetches web pages and discovers internal links."""

    def normalize_url(self, url: str, base_url: str) -> str:
        """Normalize a URL by resolving relative paths and removing fragments."""
        resolved = urllib.parse.urljoin(base_url, url)
        parsed = urllib.parse.urlparse(resolved)
        # Remove fragment
        normalized = urllib.parse.urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path,
             parsed.params, parsed.query, "")
        )
        return normalized

    def extract_links_from_html(
        self, html_content: str, base_url: str
    ) -> list[model.DiscoveredLink]:
        """Extract and normalize all links from HTML content."""
        doc = lxml.html.fromstring(html_content)
        seen_urls: set[str] = set()
        links: list[model.DiscoveredLink] = []

        for element in doc.iter("a"):
            href = element.get("href")
            if href is None:
                continue

            href = href.strip()
            if not href:
                continue

            # Skip non-HTTP schemes
            if _is_non_http_scheme(href):
                continue

            # Skip fragment-only links
            if href.startswith("#"):
                continue

            normalized = self.normalize_url(href, base_url)

            # Skip if already seen
            if normalized in seen_urls:
                continue
            seen_urls.add(normalized)

            # Extract anchor text
            text = element.text_content().strip() if element.text_content() else None
            anchor_text = text if text else None

            links.append(
                model.DiscoveredLink(url=normalized, anchor_text=anchor_text)
            )

        return links

    def filter_by_domain(
        self,
        links: list[model.DiscoveredLink],
        domain: str,
    ) -> list[model.DiscoveredLink]:
        """Filter links to keep only those on the specified domain."""
        filtered: list[model.DiscoveredLink] = []
        for link in links:
            parsed = urllib.parse.urlparse(link.url)
            link_domain = parsed.hostname or ""
            if link_domain == domain:
                filtered.append(link)
        return filtered

    def filter_by_pattern(
        self,
        links: list[model.DiscoveredLink],
        include_pattern: str | None,
        exclude_pattern: str | None,
    ) -> list[model.DiscoveredLink]:
        """Filter links by include/exclude regex patterns."""
        result = links

        if include_pattern is not None:
            compiled_include = re.compile(include_pattern)
            result = [
                link for link in result if compiled_include.search(link.url)
            ]

        if exclude_pattern is not None:
            compiled_exclude = re.compile(exclude_pattern)
            result = [
                link for link in result if not compiled_exclude.search(link.url)
            ]

        return result

    async def fetch_page(self, url: str) -> str:
        """Fetch a web page and return its HTML content."""
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "NTLMCrawler/1.0"},
            )
            response.raise_for_status()
            return response.text

    async def discover_links(
        self,
        url: str,
        domain: str,
        include_pattern: str | None = None,
        exclude_pattern: str | None = None,
    ) -> list[model.DiscoveredLink]:
        """Fetch a page and discover all internal links."""
        html_content = await self.fetch_page(url)
        links = self.extract_links_from_html(html_content, base_url=url)
        links = self.filter_by_domain(links, domain=domain)
        links = self.filter_by_pattern(
            links,
            include_pattern=include_pattern,
            exclude_pattern=exclude_pattern,
        )
        return links


def _is_non_http_scheme(href: str) -> bool:
    """Check if a URL has a non-HTTP scheme."""
    for scheme in NON_HTTP_SCHEMES:
        if href.startswith(f"{scheme}:"):
            return True
    return False
