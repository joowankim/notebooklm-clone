"""Tests for link discovery service."""

import pytest

from src.crawl.domain.model import DiscoveredLink
from src.crawl.service.link_discovery import LinkDiscoveryService


class TestNormalizeUrl:
    """Tests for URL normalization."""

    def test_absolute_url_unchanged(self) -> None:
        # Arrange
        service = LinkDiscoveryService()

        # Act
        result = service.normalize_url(
            "https://example.com/page", base_url="https://example.com"
        )

        # Assert
        assert result == "https://example.com/page"

    def test_relative_url_resolved(self) -> None:
        service = LinkDiscoveryService()
        result = service.normalize_url(
            "/page2", base_url="https://example.com/page1"
        )
        assert result == "https://example.com/page2"

    def test_relative_path_resolved(self) -> None:
        service = LinkDiscoveryService()
        result = service.normalize_url(
            "subpage", base_url="https://example.com/docs/"
        )
        assert result == "https://example.com/docs/subpage"

    def test_fragment_removed(self) -> None:
        service = LinkDiscoveryService()
        result = service.normalize_url(
            "https://example.com/page#section", base_url="https://example.com"
        )
        assert result == "https://example.com/page"

    def test_query_params_preserved(self) -> None:
        service = LinkDiscoveryService()
        result = service.normalize_url(
            "https://example.com/page?q=test", base_url="https://example.com"
        )
        assert result == "https://example.com/page?q=test"

    def test_trailing_slash_normalized(self) -> None:
        service = LinkDiscoveryService()
        result = service.normalize_url(
            "https://example.com/page/", base_url="https://example.com"
        )
        assert result == "https://example.com/page/"


class TestExtractLinksFromHtml:
    """Tests for HTML link extraction."""

    def test_extracts_absolute_links(self) -> None:
        # Arrange
        service = LinkDiscoveryService()
        html = """
        <html><body>
          <a href="https://example.com/page1">Page 1</a>
          <a href="https://example.com/page2">Page 2</a>
        </body></html>
        """

        # Act
        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        # Assert
        urls = [link.url for link in links]
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls

    def test_resolves_relative_links(self) -> None:
        service = LinkDiscoveryService()
        html = '<html><body><a href="/about">About</a></body></html>'

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        assert len(links) == 1
        assert links[0].url == "https://example.com/about"

    def test_captures_anchor_text(self) -> None:
        service = LinkDiscoveryService()
        html = '<html><body><a href="/page">Click Here</a></body></html>'

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        assert links[0].anchor_text == "Click Here"

    def test_skips_empty_anchor_text(self) -> None:
        service = LinkDiscoveryService()
        html = '<html><body><a href="/page"><img src="icon.png"/></a></body></html>'

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        assert len(links) == 1
        assert links[0].anchor_text is None

    def test_skips_mailto_links(self) -> None:
        service = LinkDiscoveryService()
        html = '<html><body><a href="mailto:test@example.com">Email</a></body></html>'

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        assert len(links) == 0

    def test_skips_javascript_links(self) -> None:
        service = LinkDiscoveryService()
        html = '<html><body><a href="javascript:void(0)">Click</a></body></html>'

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        assert len(links) == 0

    def test_skips_fragment_only_links(self) -> None:
        service = LinkDiscoveryService()
        html = '<html><body><a href="#section">Section</a></body></html>'

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        assert len(links) == 0

    def test_skips_links_without_href(self) -> None:
        service = LinkDiscoveryService()
        html = '<html><body><a name="anchor">Named</a></body></html>'

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        assert len(links) == 0

    def test_deduplicates_urls(self) -> None:
        service = LinkDiscoveryService()
        html = """
        <html><body>
          <a href="/page">Link 1</a>
          <a href="/page">Link 2</a>
          <a href="/page#section">Link 3</a>
        </body></html>
        """

        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )

        urls = [link.url for link in links]
        assert urls.count("https://example.com/page") == 1


class TestFilterByDomain:
    """Tests for domain filtering."""

    def test_keeps_same_domain(self) -> None:
        service = LinkDiscoveryService()
        links = [
            DiscoveredLink(url="https://example.com/page1", anchor_text=None),
            DiscoveredLink(url="https://other.com/page2", anchor_text=None),
        ]

        filtered = service.filter_by_domain(links, domain="example.com")

        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/page1"

    def test_keeps_subdomain(self) -> None:
        service = LinkDiscoveryService()
        links = [
            DiscoveredLink(url="https://docs.example.com/page", anchor_text=None),
        ]

        filtered = service.filter_by_domain(links, domain="docs.example.com")

        assert len(filtered) == 1

    def test_filters_out_different_subdomain(self) -> None:
        service = LinkDiscoveryService()
        links = [
            DiscoveredLink(url="https://blog.example.com/page", anchor_text=None),
        ]

        filtered = service.filter_by_domain(links, domain="docs.example.com")

        assert len(filtered) == 0


class TestFilterByPattern:
    """Tests for URL pattern filtering."""

    def test_include_pattern(self) -> None:
        service = LinkDiscoveryService()
        links = [
            DiscoveredLink(url="https://example.com/docs/intro", anchor_text=None),
            DiscoveredLink(url="https://example.com/blog/post", anchor_text=None),
        ]

        filtered = service.filter_by_pattern(
            links, include_pattern=r"/docs/.*", exclude_pattern=None
        )

        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/docs/intro"

    def test_exclude_pattern(self) -> None:
        service = LinkDiscoveryService()
        links = [
            DiscoveredLink(url="https://example.com/page.html", anchor_text=None),
            DiscoveredLink(url="https://example.com/file.pdf", anchor_text=None),
        ]

        filtered = service.filter_by_pattern(
            links, include_pattern=None, exclude_pattern=r".*\.pdf$"
        )

        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/page.html"

    def test_both_patterns(self) -> None:
        service = LinkDiscoveryService()
        links = [
            DiscoveredLink(url="https://example.com/docs/intro.html", anchor_text=None),
            DiscoveredLink(url="https://example.com/docs/file.pdf", anchor_text=None),
            DiscoveredLink(url="https://example.com/blog/post", anchor_text=None),
        ]

        filtered = service.filter_by_pattern(
            links, include_pattern=r"/docs/.*", exclude_pattern=r".*\.pdf$"
        )

        assert len(filtered) == 1
        assert filtered[0].url == "https://example.com/docs/intro.html"

    def test_no_patterns_returns_all(self) -> None:
        service = LinkDiscoveryService()
        links = [
            DiscoveredLink(url="https://example.com/page1", anchor_text=None),
            DiscoveredLink(url="https://example.com/page2", anchor_text=None),
        ]

        filtered = service.filter_by_pattern(
            links, include_pattern=None, exclude_pattern=None
        )

        assert len(filtered) == 2


class TestFetchAndDiscoverLinks:
    """Tests for the main discover_links method (with mocked HTTP)."""

    @pytest.mark.asyncio
    async def test_discover_links_filters_to_domain(self) -> None:
        # Arrange
        service = LinkDiscoveryService()
        html = """
        <html><body>
          <a href="https://example.com/page1">Internal</a>
          <a href="/page2">Relative</a>
          <a href="https://other.com/page3">External</a>
          <a href="mailto:a@b.com">Mail</a>
        </body></html>
        """

        # Act (using extract + filter directly, no HTTP)
        links = service.extract_links_from_html(
            html, base_url="https://example.com"
        )
        filtered = service.filter_by_domain(links, domain="example.com")

        # Assert
        assert len(filtered) == 2
        urls = [link.url for link in filtered]
        assert "https://example.com/page1" in urls
        assert "https://example.com/page2" in urls
