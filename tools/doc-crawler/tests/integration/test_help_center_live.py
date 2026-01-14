"""Live integration tests for Help Center adapter.

These tests hit the real help.ui.com site and verify that:
1. HTML selectors work against the current site structure
2. Discovery flow works end-to-end
3. Article content can be fetched and parsed

Run with: pytest tests/integration/test_help_center_live.py -v -m integration

NOTE: These tests use BrowserFetcher (Playwright) to bypass Cloudflare protection.
Ensure Playwright browsers are installed: playwright install chromium
"""

import pytest

from doc_crawler.adapters.help_center import HelpCenterAdapter
from doc_crawler.browser import BrowserFetcher, BrowserFetcherConfig
from doc_crawler.config import CrawlerConfig


@pytest.mark.integration
class TestHelpCenterLive:
    """Live integration tests against help.ui.com using BrowserFetcher.

    Uses Playwright to handle Cloudflare JS challenges automatically.
    """

    @pytest.fixture
    def config(self) -> CrawlerConfig:
        """Create crawler configuration with slower rate limit for browser."""
        config = CrawlerConfig()
        # Slower rate for browser-based fetching
        config.rate_limit.requests_per_second = 0.5
        return config

    @pytest.fixture
    def browser_config(self) -> BrowserFetcherConfig:
        """Create browser configuration."""
        return BrowserFetcherConfig(
            headless=True,
            timeout=60000,  # Longer timeout for Cloudflare
            cloudflare_timeout=20.0,
        )

    @pytest.mark.asyncio
    async def test_discover_sections_from_category(
        self, config: CrawlerConfig, browser_config: BrowserFetcherConfig
    ) -> None:
        """Test discovering sections from real UniFi category."""
        async with BrowserFetcher(config, browser_config) as fetcher:
            adapter = HelpCenterAdapter(config.sources.help_center, fetcher)

            sections = []
            async for section in adapter._discover_sections(
                "https://help.ui.com/hc/en-us/categories/6583256751383-UniFi"
            ):
                sections.append(section)
                if len(sections) >= 3:  # Limit for test speed
                    break

            assert len(sections) > 0, "No sections found - selectors may need updating"
            for section in sections:
                assert section.id, "Section ID should not be empty"
                assert section.name, "Section name should not be empty"
                assert "/sections/" in section.url

    @pytest.mark.asyncio
    async def test_discover_articles_from_section(
        self, config: CrawlerConfig, browser_config: BrowserFetcherConfig
    ) -> None:
        """Test discovering articles from a real section."""
        async with BrowserFetcher(config, browser_config) as fetcher:
            adapter = HelpCenterAdapter(config.sources.help_center, fetcher)

            # First, find a section
            section = None
            async for s in adapter._discover_sections(
                "https://help.ui.com/hc/en-us/categories/6583256751383-UniFi"
            ):
                section = s
                break

            if section is None:
                pytest.skip("No sections found to test articles")

            # Now find articles in that section
            articles = []
            async for article in adapter._discover_articles_in_section(
                section, max_pages=1
            ):
                articles.append(article)
                if len(articles) >= 3:
                    break

            assert len(articles) > 0, "No articles found - selectors may need updating"
            for article in articles:
                assert article.id, "Article ID should not be empty"
                assert article.title, "Article title should not be empty"
                assert "/articles/" in article.url

    @pytest.mark.asyncio
    async def test_fetch_article_content(
        self, config: CrawlerConfig, browser_config: BrowserFetcherConfig
    ) -> None:
        """Test fetching actual article content."""
        async with BrowserFetcher(config, browser_config) as fetcher:
            adapter = HelpCenterAdapter(config.sources.help_center, fetcher)

            # Find an article
            section = None
            async for s in adapter._discover_sections(
                "https://help.ui.com/hc/en-us/categories/6583256751383-UniFi"
            ):
                section = s
                break

            if section is None:
                pytest.skip("No sections found")

            article = None
            async for a in adapter._discover_articles_in_section(section, max_pages=1):
                article = a
                break

            if article is None:
                pytest.skip("No articles found")

            # Fetch the article
            content = await adapter.fetch_article(article)

            assert content is not None, "Failed to fetch article content"
            assert len(content.html_content) > 100, "HTML content seems too short"
            assert len(content.text_content) > 50, "Text content seems too short"

    @pytest.mark.asyncio
    async def test_full_discovery_limited(
        self, config: CrawlerConfig, browser_config: BrowserFetcherConfig
    ) -> None:
        """Test full discovery flow with limits."""
        async with BrowserFetcher(config, browser_config) as fetcher:
            adapter = HelpCenterAdapter(config.sources.help_center, fetcher)

            items = []
            async for item in adapter.discover():
                items.append(item)
                if len(items) >= 5:  # Stop early for test speed
                    break

            assert len(items) > 0, "No items discovered"
            for item in items:
                assert item.item_type == "article"
                metadata = item.get_metadata()
                assert "article_id" in metadata
                assert "title" in metadata

    @pytest.mark.asyncio
    async def test_article_metadata_extraction(
        self, config: CrawlerConfig, browser_config: BrowserFetcherConfig
    ) -> None:
        """Test that metadata is properly extracted from articles."""
        async with BrowserFetcher(config, browser_config) as fetcher:
            adapter = HelpCenterAdapter(config.sources.help_center, fetcher)

            # Find an article
            section = None
            async for s in adapter._discover_sections(
                "https://help.ui.com/hc/en-us/categories/6583256751383-UniFi"
            ):
                section = s
                break

            if section is None:
                pytest.skip("No sections found")

            article = None
            async for a in adapter._discover_articles_in_section(section, max_pages=1):
                article = a
                break

            if article is None:
                pytest.skip("No articles found")

            # Fetch using the CrawlItem interface
            from doc_crawler.adapters.base import CrawlItem

            item = CrawlItem.with_metadata(
                url=article.url,
                item_type="article",
                metadata={"article_id": article.id, "title": article.title},
            )

            result = await adapter.fetch(item)

            assert result.success, f"Fetch failed: {result.error}"
            metadata = result.get_metadata()

            # Title should be extracted (may be updated from HTML)
            assert "title" in metadata
            assert len(metadata["title"]) > 0

            # Content type should be HTML
            assert result.content_type == "text/html"
