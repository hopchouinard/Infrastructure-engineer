"""
Browser-based fetcher using Playwright for sites with JavaScript challenges.

This module provides a BrowserFetcher class that uses Playwright to fetch
web pages, handling Cloudflare and similar JavaScript-based anti-bot measures
that cannot be bypassed with simple HTTP requests.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Literal

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Response,
    async_playwright,
)

from .config import CrawlerConfig
from .fetcher import FetchResult, RateLimiter

__all__ = [
    "BrowserFetcher",
    "BrowserFetcherConfig",
]

logger = logging.getLogger(__name__)


@dataclass
class BrowserFetcherConfig:
    """Configuration for browser-based fetching.

    Attributes:
        headless: Run browser in headless mode (no visible window).
        timeout: Page load timeout in milliseconds.
        wait_for_cloudflare: Wait for Cloudflare challenge to complete.
        cloudflare_timeout: Max time to wait for Cloudflare in seconds.
        browser_type: Which browser to use (chromium, firefox, webkit).
        user_agent: Custom User-Agent string. Uses a realistic Chrome UA by default.
    """

    headless: bool = True
    timeout: int = 30000
    wait_for_cloudflare: bool = True
    cloudflare_timeout: float = 15.0
    browser_type: Literal["chromium", "firefox", "webkit"] = "chromium"
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )


@dataclass
class BrowserFetcher:
    """Browser-based fetcher using Playwright.

    Provides the same interface as Fetcher but uses a real browser to
    handle JavaScript challenges like Cloudflare. This allows fetching
    from sites that block simple HTTP requests.

    Must be used as an async context manager:

        async with BrowserFetcher(config) as fetcher:
            result = await fetcher.get("https://example.com")

    Attributes:
        config: Crawler configuration.
        browser_config: Browser-specific configuration.
    """

    config: CrawlerConfig
    browser_config: BrowserFetcherConfig = field(default_factory=BrowserFetcherConfig)

    # Internal state (initialized in __aenter__)
    _playwright: Playwright | None = field(default=None, init=False, repr=False)
    _browser: Browser | None = field(default=None, init=False, repr=False)
    _context: BrowserContext | None = field(default=None, init=False, repr=False)
    _rate_limiter: RateLimiter = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize rate limiter after dataclass init."""
        self._rate_limiter = RateLimiter(self.config.rate_limit.requests_per_second)

    async def __aenter__(self) -> "BrowserFetcher":
        """Enter async context and launch browser."""
        self._playwright = await async_playwright().start()

        # Select browser type
        browser_launcher = getattr(self._playwright, self.browser_config.browser_type)
        self._browser = await browser_launcher.launch(
            headless=self.browser_config.headless,
        )

        # Create context with realistic settings
        self._context = await self._browser.new_context(
            user_agent=self.browser_config.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )

        logger.info("Browser launched: %s (headless=%s)",
                    self.browser_config.browser_type,
                    self.browser_config.headless)

        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object,
    ) -> None:
        """Exit async context and close browser."""
        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Browser closed")

    async def _wait_for_cloudflare(self, page: Page) -> bool:
        """Wait for Cloudflare challenge to complete.

        Args:
            page: Playwright page instance.

        Returns:
            True if challenge completed, False if timeout.
        """
        start = time.monotonic()
        timeout = self.browser_config.cloudflare_timeout

        while time.monotonic() - start < timeout:
            # Check page content for Cloudflare indicators
            content = await page.content()

            # Cloudflare challenge page indicators
            cloudflare_indicators = (
                "Just a moment",
                "Checking your browser",
                "cf-browser-verification",
                "challenge-platform",
            )
            is_challenge = any(indicator in content for indicator in cloudflare_indicators)

            if not is_challenge:
                logger.debug("Cloudflare challenge completed")
                return True

            # Wait a bit before checking again
            await asyncio.sleep(0.5)

        logger.warning("Cloudflare challenge timeout after %.1fs", timeout)
        return False

    async def get(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> FetchResult:
        """Fetch a URL using the browser.

        Args:
            url: URL to fetch.
            max_retries: Maximum retry attempts (for network errors).
            retry_delay: Delay between retries in seconds.

        Returns:
            FetchResult with page content.

        Raises:
            RuntimeError: If not used as async context manager.
        """
        if not self._context:
            raise RuntimeError("BrowserFetcher must be used as async context manager")

        last_error: str | None = None

        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                await self._rate_limiter.acquire()

                start = time.monotonic()

                # Create new page for this request
                page = await self._context.new_page()

                try:
                    # Navigate to URL
                    response: Response | None = await page.goto(
                        url,
                        timeout=self.browser_config.timeout,
                        wait_until="domcontentloaded",
                    )

                    # Wait for Cloudflare if enabled
                    if self.browser_config.wait_for_cloudflare:
                        await self._wait_for_cloudflare(page)

                    # Get final content after any JS execution
                    content = await page.content()
                    elapsed = (time.monotonic() - start) * 1000

                    # Build result
                    status_code = response.status if response else 200
                    headers = dict(response.headers) if response else {}

                    return FetchResult(
                        url=page.url,  # May differ due to redirects
                        status_code=status_code,
                        content=content.encode("utf-8"),
                        content_type=headers.get("content-type", "text/html"),
                        headers=headers,
                        success=200 <= status_code < 400,
                        elapsed_ms=elapsed,
                    )

                finally:
                    await page.close()

            except Exception as e:
                last_error = f"Browser error: {e}"
                logger.warning("Fetch attempt %d failed: %s", attempt + 1, last_error)

                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (2**attempt))
                    continue

        # All retries exhausted
        return FetchResult(
            url=url,
            status_code=0,
            content=b"",
            content_type="",
            headers={},
            success=False,
            error=last_error or "Unknown error",
        )

    async def get_text(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> tuple[str, FetchResult]:
        """Fetch URL and return content as text.

        Args:
            url: URL to fetch.
            max_retries: Maximum retry attempts.
            retry_delay: Delay between retries in seconds.

        Returns:
            Tuple of (text_content, FetchResult).
        """
        result = await self.get(url, max_retries=max_retries, retry_delay=retry_delay)

        if not result.success:
            return "", result

        # Decode content
        try:
            text = result.content.decode("utf-8")
        except UnicodeDecodeError:
            text = result.content.decode("utf-8", errors="replace")

        return text, result

    async def head(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> FetchResult:
        """Check URL accessibility (makes full request, browser limitation).

        Note: Browsers don't support true HEAD requests, so this makes
        a full GET request but only returns headers.

        Args:
            url: URL to check.
            max_retries: Maximum retry attempts.
            retry_delay: Delay between retries in seconds.

        Returns:
            FetchResult with headers but minimal content info.
        """
        result = await self.get(url, max_retries=max_retries, retry_delay=retry_delay)

        # Return result with empty content (simulating HEAD)
        return FetchResult(
            url=result.url,
            status_code=result.status_code,
            content=b"",  # HEAD doesn't return body
            content_type=result.content_type,
            headers=result.headers,
            success=result.success,
            error=result.error,
            elapsed_ms=result.elapsed_ms,
        )

    @staticmethod
    def is_cloudflare_blocked(result: FetchResult) -> bool:
        """Check if a FetchResult indicates Cloudflare blocking.

        Useful for deciding whether to switch from Fetcher to BrowserFetcher.

        Args:
            result: FetchResult from a regular Fetcher.

        Returns:
            True if the result indicates Cloudflare JS challenge.
        """
        if result.status_code == 403:
            content = result.content.decode("utf-8", errors="replace")
            cloudflare_indicators = (
                "Just a moment",
                "Checking your browser",
                "cf-browser-verification",
            )
            return any(indicator in content for indicator in cloudflare_indicators)
        return False
