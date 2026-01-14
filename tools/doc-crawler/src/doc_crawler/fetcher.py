"""
HTTP fetcher with rate limiting, retry logic, and robots.txt compliance.

Provides a robust HTTP client for fetching documentation pages with:
- Configurable rate limiting (token bucket algorithm)
- Automatic retry with exponential backoff
- robots.txt compliance (cached per domain)
- Request/response timing metrics
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from .config import CrawlerConfig

__all__ = [
    "FetchResult",
    "Fetcher",
    "FetcherProtocol",
    "RateLimiter",
    "RobotsChecker",
]


@runtime_checkable
class FetcherProtocol(Protocol):
    """Protocol defining the fetcher interface.

    Both Fetcher (HTTP-based) and BrowserFetcher (Playwright-based)
    implement this interface, allowing adapters to use either.
    """

    async def get(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> "FetchResult":
        """Fetch a URL and return the result."""
        ...

    async def get_text(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> tuple[str, "FetchResult"]:
        """Fetch a URL and return content as text."""
        ...

    async def head(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> "FetchResult":
        """Make a HEAD request to check URL."""
        ...


@dataclass
class FetchResult:
    """Result of a fetch operation.

    Attributes:
        url: The final URL (may differ from requested URL due to redirects).
        status_code: HTTP status code (0 if request failed before response).
        content: Response body as bytes.
        content_type: Content-Type header value.
        headers: All response headers.
        success: True if status code is 2xx or 3xx.
        error: Error message if request failed.
        elapsed_ms: Request duration in milliseconds.
    """

    url: str
    status_code: int
    content: bytes
    content_type: str
    headers: dict[str, str]
    success: bool
    error: str | None = None
    elapsed_ms: float = 0.0


@dataclass
class RateLimiter:
    """Token bucket rate limiter for controlling request frequency.

    Uses a simple token bucket algorithm where tokens are replenished
    at a fixed rate. Each request consumes one token.

    Attributes:
        requests_per_second: Maximum requests allowed per second.
    """

    requests_per_second: float
    # Initialize to 0 so first request is immediate (monotonic time starts > 0)
    _last_request: float = field(default=0.0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @property
    def min_interval(self) -> float:
        """Minimum interval between requests in seconds."""
        return 1.0 / self.requests_per_second

    async def acquire(self) -> None:
        """Wait until a request can be made.

        This method blocks until enough time has passed since the last
        request to satisfy the rate limit.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            wait_time = self.min_interval - elapsed

            if wait_time > 0:
                await asyncio.sleep(wait_time)

            self._last_request = time.monotonic()


class RobotsChecker:
    """Checks robots.txt compliance for URLs.

    Caches robots.txt files per domain to avoid repeated fetches.
    Gracefully handles missing or inaccessible robots.txt files
    by allowing all requests in those cases.

    Attributes:
        user_agent: The User-Agent string to check rules against.
    """

    def __init__(self, user_agent: str, timeout: float = 10.0) -> None:
        """Initialize the robots checker.

        Args:
            user_agent: User-Agent string to check robots.txt rules against.
            timeout: Timeout in seconds for fetching robots.txt files.
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self._parsers: dict[str, RobotFileParser] = {}
        self._lock = asyncio.Lock()

    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    async def can_fetch(self, url: str, client: httpx.AsyncClient) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: The URL to check.
            client: HTTP client to use for fetching robots.txt.

        Returns:
            True if the URL can be fetched, False if blocked by robots.txt.
        """
        robots_url = self._get_robots_url(url)

        async with self._lock:
            if robots_url not in self._parsers:
                parser = RobotFileParser()
                try:
                    response = await client.get(robots_url, timeout=self.timeout)
                    if response.status_code == 200:
                        parser.parse(response.text.splitlines())
                    else:
                        # No robots.txt or error - allow all
                        parser.allow_all = True  # type: ignore[attr-defined]
                except (httpx.RequestError, httpx.TimeoutException):
                    # Can't fetch robots.txt - allow all
                    parser.allow_all = True  # type: ignore[attr-defined]

                self._parsers[robots_url] = parser

        parser = self._parsers[robots_url]

        # Handle case where parser has allow_all attribute (our addition)
        if getattr(parser, "allow_all", False):
            return True

        return parser.can_fetch(self.user_agent, url)


class Fetcher:
    """HTTP fetcher with rate limiting and retry logic.

    Provides a robust way to fetch URLs with:
    - Rate limiting to avoid overwhelming servers
    - Automatic retries with exponential backoff for transient errors
    - robots.txt compliance (optional)
    - Redirect following
    - Timeout handling

    Must be used as an async context manager:

        async with Fetcher(config) as fetcher:
            result = await fetcher.get("https://example.com")

    Attributes:
        config: Crawler configuration.
        user_agent: User-Agent string for requests.
    """

    DEFAULT_USER_AGENT = (
        "UniFi-Doc-Crawler/1.0 (+https://github.com/hopchouinard/Infrastructure-engineer)"
    )

    def __init__(
        self,
        config: CrawlerConfig,
        user_agent: str | None = None,
    ) -> None:
        """Initialize the fetcher.

        Args:
            config: Crawler configuration with rate limit settings.
            user_agent: Custom User-Agent string. Uses default if not provided.
        """
        self.config = config
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT

        self._client: httpx.AsyncClient | None = None
        self._rate_limiter = RateLimiter(config.rate_limit.requests_per_second)
        self._robots_checker: RobotsChecker | None = None

        if config.rate_limit.respect_robots_txt:
            self._robots_checker = RobotsChecker(
                self.user_agent,
                timeout=config.rate_limit.robots_timeout,
            )

    async def __aenter__(self) -> "Fetcher":
        """Enter async context and create HTTP client."""
        self._client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
            timeout=self.config.rate_limit.request_timeout,
        )
        return self

    async def __aexit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object,
    ) -> None:
        """Exit async context and close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> FetchResult:
        """Fetch a URL with rate limiting and retry logic.

        Args:
            url: URL to fetch.
            max_retries: Maximum number of retry attempts for transient errors.
            retry_delay: Initial delay between retries in seconds (doubles each retry).

        Returns:
            FetchResult with response data or error information.

        Raises:
            RuntimeError: If fetcher is not used as async context manager.
        """
        if not self._client:
            raise RuntimeError("Fetcher must be used as async context manager")

        # Check robots.txt
        if self._robots_checker and not await self._robots_checker.can_fetch(
            url, self._client
        ):
            return FetchResult(
                url=url,
                status_code=0,
                content=b"",
                content_type="",
                headers={},
                success=False,
                error="Blocked by robots.txt",
            )

        # Retry loop
        last_error: str | None = None
        for attempt in range(max_retries + 1):
            try:
                # Rate limiting
                await self._rate_limiter.acquire()

                # Make request
                start = time.monotonic()
                response = await self._client.get(url)
                elapsed = (time.monotonic() - start) * 1000

                # Handle response
                if response.status_code == 429:
                    # Rate limited by server - counts against retries to prevent infinite loop
                    if attempt < max_retries:
                        retry_after = float(
                            response.headers.get("Retry-After", retry_delay)
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    # Final attempt still got 429
                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        content=response.content,
                        content_type=response.headers.get("content-type", ""),
                        headers=dict(response.headers),
                        success=False,
                        error="Rate limited by server (429)",
                        elapsed_ms=elapsed,
                    )

                if response.status_code >= 500:
                    # Server error - retry
                    last_error = f"Server error: {response.status_code}"
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay * (2**attempt))
                        continue
                    # Final attempt failed with server error
                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        content=response.content,
                        content_type=response.headers.get("content-type", ""),
                        headers=dict(response.headers),
                        success=False,
                        error=last_error,
                        elapsed_ms=elapsed,
                    )

                # Success or client error (don't retry 4xx except 429)
                return FetchResult(
                    url=str(response.url),  # May differ due to redirects
                    status_code=response.status_code,
                    content=response.content,
                    content_type=response.headers.get("content-type", ""),
                    headers=dict(response.headers),
                    success=200 <= response.status_code < 400,
                    elapsed_ms=elapsed,
                )

            except httpx.TimeoutException:
                last_error = "Request timed out"
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (2**attempt))
                    continue

            except httpx.RequestError as e:
                last_error = f"Request failed: {e}"
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

        Automatically detects encoding from Content-Type header.
        Falls back to UTF-8 with replacement for invalid characters.

        Args:
            url: URL to fetch.
            max_retries: Maximum number of retry attempts for transient errors.
            retry_delay: Initial delay between retries in seconds (doubles each retry).

        Returns:
            Tuple of (text_content, FetchResult).
        """
        result = await self.get(url, max_retries=max_retries, retry_delay=retry_delay)

        if not result.success:
            return "", result

        # Detect encoding
        encoding = "utf-8"
        content_type = result.content_type.lower()
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].split(";")[0].strip()

        try:
            text = result.content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            text = result.content.decode("utf-8", errors="replace")

        return text, result

    async def head(
        self,
        url: str,
        *,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> FetchResult:
        """Make a HEAD request to check URL without downloading content.

        Useful for checking if a URL exists or getting content metadata
        without downloading the full response body.

        Args:
            url: URL to check.
            max_retries: Maximum number of retry attempts for transient errors.
            retry_delay: Initial delay between retries in seconds (doubles each retry).

        Returns:
            FetchResult with headers but empty content.

        Raises:
            RuntimeError: If fetcher is not used as async context manager.
        """
        if not self._client:
            raise RuntimeError("Fetcher must be used as async context manager")

        # Check robots.txt
        if self._robots_checker and not await self._robots_checker.can_fetch(
            url, self._client
        ):
            return FetchResult(
                url=url,
                status_code=0,
                content=b"",
                content_type="",
                headers={},
                success=False,
                error="Blocked by robots.txt",
            )

        # Retry loop
        last_error: str | None = None
        for attempt in range(max_retries + 1):
            try:
                await self._rate_limiter.acquire()

                start = time.monotonic()
                response = await self._client.head(url)
                elapsed = (time.monotonic() - start) * 1000

                # Retry on server errors
                if response.status_code >= 500:
                    last_error = f"Server error: {response.status_code}"
                    if attempt < max_retries:
                        await asyncio.sleep(retry_delay * (2**attempt))
                        continue
                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        content=b"",
                        content_type=response.headers.get("content-type", ""),
                        headers=dict(response.headers),
                        success=False,
                        error=last_error,
                        elapsed_ms=elapsed,
                    )

                return FetchResult(
                    url=str(response.url),
                    status_code=response.status_code,
                    content=b"",
                    content_type=response.headers.get("content-type", ""),
                    headers=dict(response.headers),
                    success=200 <= response.status_code < 400,
                    elapsed_ms=elapsed,
                )

            except httpx.TimeoutException:
                last_error = "Request timed out"
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (2**attempt))
                    continue

            except httpx.RequestError as e:
                last_error = f"Request failed: {e}"
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
