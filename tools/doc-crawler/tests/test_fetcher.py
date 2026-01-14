"""Tests for the HTTP fetcher module."""

import asyncio

import httpx
import pytest
from respx import MockRouter

from doc_crawler.config import CrawlerConfig, RateLimitConfig
from doc_crawler.fetcher import Fetcher, FetchResult, RateLimiter, RobotsChecker


class TestRateLimiter:
    """Tests for the rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_spacing(self) -> None:
        """Test that rate limiter spaces requests correctly."""
        limiter = RateLimiter(requests_per_second=10.0)  # 100ms between requests

        start = asyncio.get_event_loop().time()

        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()

        elapsed = asyncio.get_event_loop().time() - start

        # Should take at least 200ms for 3 requests at 10/s
        assert elapsed >= 0.18  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_rate_limiter_first_request_immediate(self) -> None:
        """Test that first request is immediate."""
        limiter = RateLimiter(requests_per_second=1.0)

        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start

        # First request should be nearly instant
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent_safe(self) -> None:
        """Test that rate limiter handles concurrent requests."""
        limiter = RateLimiter(requests_per_second=10.0)

        # Launch multiple concurrent acquires
        await asyncio.gather(*[limiter.acquire() for _ in range(5)])

        # Should complete without error (lock prevents race conditions)

    def test_min_interval_property(self) -> None:
        """Test min_interval property calculation."""
        limiter = RateLimiter(requests_per_second=2.0)
        assert limiter.min_interval == 0.5

        limiter = RateLimiter(requests_per_second=10.0)
        assert limiter.min_interval == 0.1


class TestRobotsChecker:
    """Tests for robots.txt checking."""

    @pytest.mark.asyncio
    async def test_robots_allows_when_no_robots(self, respx_mock: MockRouter) -> None:
        """Test that missing robots.txt allows all."""
        respx_mock.get("https://example.com/robots.txt").respond(status_code=404)

        checker = RobotsChecker("TestBot/1.0")

        async with httpx.AsyncClient() as client:
            allowed = await checker.can_fetch("https://example.com/page", client)

        assert allowed is True

    @pytest.mark.asyncio
    async def test_robots_blocks_disallowed_path(self, respx_mock: MockRouter) -> None:
        """Test that disallowed paths are blocked."""
        robots_txt = """
User-agent: *
Disallow: /private/
"""
        respx_mock.get("https://example.com/robots.txt").respond(
            text=robots_txt,
            status_code=200,
        )

        checker = RobotsChecker("TestBot/1.0")

        async with httpx.AsyncClient() as client:
            allowed = await checker.can_fetch("https://example.com/private/secret", client)

        assert allowed is False

    @pytest.mark.asyncio
    async def test_robots_allows_permitted_path(self, respx_mock: MockRouter) -> None:
        """Test that allowed paths are permitted."""
        robots_txt = """
User-agent: *
Disallow: /private/
Allow: /public/
"""
        respx_mock.get("https://example.com/robots.txt").respond(
            text=robots_txt,
            status_code=200,
        )

        checker = RobotsChecker("TestBot/1.0")

        async with httpx.AsyncClient() as client:
            allowed = await checker.can_fetch("https://example.com/public/page", client)

        assert allowed is True

    @pytest.mark.asyncio
    async def test_robots_caches_result(self, respx_mock: MockRouter) -> None:
        """Test that robots.txt is cached per domain."""
        route = respx_mock.get("https://example.com/robots.txt").respond(
            text="User-agent: *\nAllow: /",
            status_code=200,
        )

        checker = RobotsChecker("TestBot/1.0")

        async with httpx.AsyncClient() as client:
            await checker.can_fetch("https://example.com/page1", client)
            await checker.can_fetch("https://example.com/page2", client)

        # Should only fetch robots.txt once
        assert route.call_count == 1

    @pytest.mark.asyncio
    async def test_robots_handles_fetch_error(self, respx_mock: MockRouter) -> None:
        """Test that fetch errors allow all requests."""
        respx_mock.get("https://example.com/robots.txt").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        checker = RobotsChecker("TestBot/1.0")

        async with httpx.AsyncClient() as client:
            allowed = await checker.can_fetch("https://example.com/page", client)

        assert allowed is True

    @pytest.mark.asyncio
    async def test_robots_different_domains_separate_cache(
        self, respx_mock: MockRouter
    ) -> None:
        """Test that different domains have separate cache entries."""
        respx_mock.get("https://example.com/robots.txt").respond(
            text="User-agent: *\nDisallow: /",
            status_code=200,
        )
        respx_mock.get("https://other.com/robots.txt").respond(
            text="User-agent: *\nAllow: /",
            status_code=200,
        )

        checker = RobotsChecker("TestBot/1.0")

        async with httpx.AsyncClient() as client:
            allowed_example = await checker.can_fetch("https://example.com/page", client)
            allowed_other = await checker.can_fetch("https://other.com/page", client)

        assert allowed_example is False
        assert allowed_other is True


class TestFetchResult:
    """Tests for the FetchResult dataclass."""

    def test_create_successful_result(self) -> None:
        """Test creating a successful fetch result."""
        result = FetchResult(
            url="https://example.com",
            status_code=200,
            content=b"Hello",
            content_type="text/html",
            headers={"content-type": "text/html"},
            success=True,
        )
        assert result.success is True
        assert result.error is None
        assert result.elapsed_ms == 0.0

    def test_create_failed_result(self) -> None:
        """Test creating a failed fetch result."""
        result = FetchResult(
            url="https://example.com",
            status_code=0,
            content=b"",
            content_type="",
            headers={},
            success=False,
            error="Connection refused",
        )
        assert result.success is False
        assert result.error == "Connection refused"


class TestFetcher:
    """Tests for the HTTP fetcher."""

    @pytest.fixture
    def config(self) -> CrawlerConfig:
        """Create test configuration."""
        return CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,  # Fast for tests
                respect_robots_txt=False,  # Disable for unit tests
            )
        )

    @pytest.mark.asyncio
    async def test_successful_fetch(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test successful URL fetch."""
        respx_mock.get("https://example.com/page").respond(
            content=b"Hello, World!",
            status_code=200,
            headers={"Content-Type": "text/html"},
        )

        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://example.com/page")

        assert result.success is True
        assert result.status_code == 200
        assert result.content == b"Hello, World!"
        assert "text/html" in result.content_type

    @pytest.mark.asyncio
    async def test_fetch_404_error(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test handling of 404 error."""
        respx_mock.get("https://example.com/notfound").respond(status_code=404)

        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://example.com/notfound")

        assert result.success is False
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_fetch_retry_on_500(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that 500 errors trigger retry."""
        route = respx_mock.get("https://example.com/flaky")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(200, content=b"Success"),
        ]

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/flaky",
                max_retries=3,
                retry_delay=0.01,  # Fast for tests
            )

        assert result.success is True
        assert result.content == b"Success"
        assert route.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_no_retry_on_400(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that 400 errors don't trigger retry."""
        route = respx_mock.get("https://example.com/bad").respond(status_code=400)

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/bad",
                max_retries=3,
            )

        assert result.success is False
        assert result.status_code == 400
        assert route.call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_fetch_timeout_retry(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that timeouts trigger retry."""
        route = respx_mock.get("https://example.com/slow")
        route.side_effect = [
            httpx.TimeoutException("Timeout"),
            httpx.Response(200, content=b"Eventually"),
        ]

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/slow",
                max_retries=2,
                retry_delay=0.01,
            )

        assert result.success is True
        assert result.content == b"Eventually"

    @pytest.mark.asyncio
    async def test_fetch_max_retries_exhausted(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test behavior when max retries exhausted."""
        respx_mock.get("https://example.com/fail").respond(status_code=500)

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/fail",
                max_retries=2,
                retry_delay=0.01,
            )

        assert result.success is False
        assert result.error is not None
        assert "Server error" in result.error

    @pytest.mark.asyncio
    async def test_fetch_connection_error_retry(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that connection errors trigger retry."""
        route = respx_mock.get("https://example.com/conn")
        route.side_effect = [
            httpx.ConnectError("Connection refused"),
            httpx.Response(200, content=b"Connected"),
        ]

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/conn",
                max_retries=2,
                retry_delay=0.01,
            )

        assert result.success is True
        assert result.content == b"Connected"

    @pytest.mark.asyncio
    async def test_get_text(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test fetching URL as text."""
        respx_mock.get("https://example.com/text").respond(
            content="Hello, UTF-8 World! \u4f60\u597d",
            status_code=200,
            headers={"Content-Type": "text/html; charset=utf-8"},
        )

        async with Fetcher(config) as fetcher:
            text, result = await fetcher.get_text("https://example.com/text")

        assert result.success is True
        assert "Hello" in text
        assert "\u4f60\u597d" in text

    @pytest.mark.asyncio
    async def test_get_text_with_encoding(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test text fetching with different encoding."""
        # ISO-8859-1 encoded content
        content = "Caf\xe9".encode("iso-8859-1")
        respx_mock.get("https://example.com/latin").respond(
            content=content,
            status_code=200,
            headers={"Content-Type": "text/html; charset=iso-8859-1"},
        )

        async with Fetcher(config) as fetcher:
            text, result = await fetcher.get_text("https://example.com/latin")

        assert result.success is True
        assert "Caf\xe9" in text

    @pytest.mark.asyncio
    async def test_get_text_failed_request(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test get_text with failed request returns empty string."""
        respx_mock.get("https://example.com/fail").respond(status_code=500)

        async with Fetcher(config) as fetcher:
            text, result = await fetcher.get_text(
                "https://example.com/fail",
                max_retries=0,
            )

        assert result.success is False
        assert text == ""

    @pytest.mark.asyncio
    async def test_robots_blocked(self, respx_mock: MockRouter) -> None:
        """Test that robots.txt blocking works."""
        robots_txt = "User-agent: *\nDisallow: /"
        respx_mock.get("https://example.com/robots.txt").respond(text=robots_txt)

        config = CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,
                respect_robots_txt=True,  # Enable for this test
            )
        )

        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://example.com/blocked")

        assert result.success is False
        assert result.error is not None
        assert "robots.txt" in result.error

    @pytest.mark.asyncio
    async def test_head_request(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test HEAD request."""
        respx_mock.head("https://example.com/file.pdf").respond(
            status_code=200,
            headers={"Content-Type": "application/pdf", "Content-Length": "12345"},
        )

        async with Fetcher(config) as fetcher:
            result = await fetcher.head("https://example.com/file.pdf")

        assert result.success is True
        assert result.content == b""  # HEAD returns no body
        assert "application/pdf" in result.content_type

    @pytest.mark.asyncio
    async def test_head_request_error(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test HEAD request with error."""
        respx_mock.head("https://example.com/error").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        async with Fetcher(config) as fetcher:
            result = await fetcher.head("https://example.com/error")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_follows_redirects(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that redirects are followed."""
        respx_mock.get("https://example.com/old").respond(
            status_code=301,
            headers={"Location": "https://example.com/new"},
        )
        respx_mock.get("https://example.com/new").respond(
            content=b"New location",
            status_code=200,
        )

        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://example.com/old")

        assert result.success is True
        assert result.url == "https://example.com/new"
        assert result.content == b"New location"

    @pytest.mark.asyncio
    async def test_elapsed_time_recorded(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that elapsed time is recorded."""
        respx_mock.get("https://example.com/time").respond(
            content=b"OK",
            status_code=200,
        )

        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://example.com/time")

        assert result.success is True
        assert result.elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_custom_user_agent(self, respx_mock: MockRouter) -> None:
        """Test custom user agent."""
        route = respx_mock.get("https://example.com/ua").respond(status_code=200)

        config = CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,
                respect_robots_txt=False,
            )
        )

        async with Fetcher(config, user_agent="CustomBot/2.0") as fetcher:
            await fetcher.get("https://example.com/ua")

        # Check the request was made with custom user agent
        assert route.calls[0].request.headers["user-agent"] == "CustomBot/2.0"

    @pytest.mark.asyncio
    async def test_default_user_agent(self, respx_mock: MockRouter) -> None:
        """Test default user agent."""
        route = respx_mock.get("https://example.com/ua").respond(status_code=200)

        config = CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,
                respect_robots_txt=False,
            )
        )

        async with Fetcher(config) as fetcher:
            await fetcher.get("https://example.com/ua")

        # Check the request was made with default user agent
        assert "UniFi-Doc-Crawler" in route.calls[0].request.headers["user-agent"]


class TestFetcherContextManager:
    """Tests for fetcher context manager behavior."""

    @pytest.mark.asyncio
    async def test_must_use_context_manager_get(self) -> None:
        """Test that fetcher raises error if get() called without context manager."""
        config = CrawlerConfig()
        fetcher = Fetcher(config)

        with pytest.raises(RuntimeError, match="context manager"):
            await fetcher.get("https://example.com")

    @pytest.mark.asyncio
    async def test_must_use_context_manager_head(self) -> None:
        """Test that fetcher raises error if head() called without context manager."""
        config = CrawlerConfig()
        fetcher = Fetcher(config)

        with pytest.raises(RuntimeError, match="context manager"):
            await fetcher.head("https://example.com")

    @pytest.mark.asyncio
    async def test_cleanup_on_exit(self) -> None:
        """Test that client is properly cleaned up."""
        config = CrawlerConfig()

        async with Fetcher(config) as fetcher:
            assert fetcher._client is not None

        assert fetcher._client is None

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(self, respx_mock: MockRouter) -> None:
        """Test that client is cleaned up even on exception."""
        config = CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,
                respect_robots_txt=False,
            )
        )

        respx_mock.get("https://example.com/").respond(status_code=200)

        fetcher = Fetcher(config)
        try:
            async with fetcher:
                assert fetcher._client is not None
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert fetcher._client is None


class TestFetcherRetryBehavior:
    """Tests for specific retry scenarios."""

    @pytest.fixture
    def config(self) -> CrawlerConfig:
        """Create test configuration."""
        return CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,
                respect_robots_txt=False,
            )
        )

    @pytest.mark.asyncio
    async def test_429_respects_retry_after(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that 429 response respects Retry-After header."""
        route = respx_mock.get("https://example.com/rate")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0.01"}),
            httpx.Response(200, content=b"OK"),
        ]

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/rate",
                max_retries=2,
            )

        assert result.success is True
        assert route.call_count == 2

    @pytest.mark.asyncio
    async def test_exponential_backoff(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that retry delay doubles each attempt."""
        import time

        route = respx_mock.get("https://example.com/backoff")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(200, content=b"OK"),
        ]

        start = time.monotonic()
        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/backoff",
                max_retries=3,
                retry_delay=0.05,  # 50ms, then 100ms
            )
        elapsed = time.monotonic() - start

        assert result.success is True
        # Should have waited at least 50ms + 100ms = 150ms
        assert elapsed >= 0.14  # Allow small tolerance

    @pytest.mark.asyncio
    async def test_no_retry_on_403(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that 403 (client error) doesn't retry."""
        route = respx_mock.get("https://example.com/forbidden").respond(status_code=403)

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/forbidden",
                max_retries=3,
            )

        assert result.success is False
        assert result.status_code == 403
        assert route.call_count == 1

    @pytest.mark.asyncio
    async def test_429_counts_against_retries(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that 429 responses count against max_retries to prevent infinite loop."""
        route = respx_mock.get("https://example.com/rate")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0.01"}),
            httpx.Response(429, headers={"Retry-After": "0.01"}),
            httpx.Response(429, headers={"Retry-After": "0.01"}),
            httpx.Response(429, headers={"Retry-After": "0.01"}),
        ]

        async with Fetcher(config) as fetcher:
            result = await fetcher.get(
                "https://example.com/rate",
                max_retries=2,
                retry_delay=0.01,
            )

        assert result.success is False
        assert result.status_code == 429
        assert result.error == "Rate limited by server (429)"
        # Should only try 3 times (initial + 2 retries)
        assert route.call_count == 3


class TestHeadRetryBehavior:
    """Tests for HEAD request retry and robots.txt behavior."""

    @pytest.fixture
    def config(self) -> CrawlerConfig:
        """Create test configuration."""
        return CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,
                respect_robots_txt=False,
            )
        )

    @pytest.mark.asyncio
    async def test_head_retry_on_500(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that HEAD requests retry on 500 errors."""
        route = respx_mock.head("https://example.com/flaky")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(200, headers={"Content-Type": "text/html"}),
        ]

        async with Fetcher(config) as fetcher:
            result = await fetcher.head(
                "https://example.com/flaky",
                max_retries=3,
                retry_delay=0.01,
            )

        assert result.success is True
        assert route.call_count == 3

    @pytest.mark.asyncio
    async def test_head_robots_blocked(self, respx_mock: MockRouter) -> None:
        """Test that HEAD requests respect robots.txt."""
        robots_txt = "User-agent: *\nDisallow: /"
        respx_mock.get("https://example.com/robots.txt").respond(text=robots_txt)

        config = CrawlerConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=100.0,
                respect_robots_txt=True,
            )
        )

        async with Fetcher(config) as fetcher:
            result = await fetcher.head("https://example.com/blocked")

        assert result.success is False
        assert result.error is not None
        assert "robots.txt" in result.error

    @pytest.mark.asyncio
    async def test_head_timeout_retry(
        self, config: CrawlerConfig, respx_mock: MockRouter
    ) -> None:
        """Test that HEAD requests retry on timeout."""
        route = respx_mock.head("https://example.com/slow")
        route.side_effect = [
            httpx.TimeoutException("Timeout"),
            httpx.Response(200),
        ]

        async with Fetcher(config) as fetcher:
            result = await fetcher.head(
                "https://example.com/slow",
                max_retries=2,
                retry_delay=0.01,
            )

        assert result.success is True
