"""Integration tests that hit real websites.

These tests are marked with @pytest.mark.integration and should be run sparingly
to avoid overwhelming external servers.

Run with: pytest tests/integration/ -v -m integration
"""

import pytest

from doc_crawler.config import CrawlerConfig, RateLimitConfig
from doc_crawler.fetcher import Fetcher


@pytest.mark.integration
class TestFetcherLive:
    """Integration tests that hit real websites."""

    @pytest.fixture
    def config(self) -> CrawlerConfig:
        """Create config for live tests."""
        return CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=0.5,  # Be polite to external servers
                respect_robots_txt=True,
            )
        )

    @pytest.mark.asyncio
    async def test_fetch_real_page(self, config: CrawlerConfig) -> None:
        """Test fetching a real webpage."""
        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://httpbin.org/get")

        assert result.success is True
        assert result.status_code == 200
        assert b"httpbin" in result.content.lower()

    @pytest.mark.asyncio
    async def test_fetch_with_user_agent(self, config: CrawlerConfig) -> None:
        """Test that user agent is sent correctly."""
        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://httpbin.org/user-agent")

        assert result.success is True
        assert b"UniFi-Doc-Crawler" in result.content

    @pytest.mark.asyncio
    async def test_fetch_respects_robots(self, config: CrawlerConfig) -> None:
        """Test that robots.txt is respected on real site."""
        async with Fetcher(config) as fetcher:
            # httpbin.org allows all, so this should succeed
            result = await fetcher.get("https://httpbin.org/robots.txt")

        assert result.success is True

    @pytest.mark.asyncio
    async def test_fetch_follows_redirect(self, config: CrawlerConfig) -> None:
        """Test following redirects on real site."""
        async with Fetcher(config) as fetcher:
            # httpbin provides a redirect endpoint
            result = await fetcher.get("https://httpbin.org/redirect/1")

        assert result.success is True
        # URL should have changed after redirect
        assert "redirect" not in result.url or "get" in result.url

    @pytest.mark.asyncio
    async def test_fetch_handles_404(self, config: CrawlerConfig) -> None:
        """Test handling 404 on real site."""
        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://httpbin.org/status/404")

        assert result.success is False
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_head_request_real(self, config: CrawlerConfig) -> None:
        """Test HEAD request on real site."""
        async with Fetcher(config) as fetcher:
            result = await fetcher.head("https://httpbin.org/get")

        assert result.success is True
        assert result.content == b""  # HEAD returns no body

    @pytest.mark.asyncio
    async def test_get_text_real(self, config: CrawlerConfig) -> None:
        """Test fetching text content from real site."""
        async with Fetcher(config) as fetcher:
            text, result = await fetcher.get_text("https://httpbin.org/html")

        assert result.success is True
        assert "html" in text.lower()
        assert "Herman Melville" in text  # httpbin returns Moby Dick excerpt
