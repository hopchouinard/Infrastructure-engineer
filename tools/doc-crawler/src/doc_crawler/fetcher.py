"""
HTTP fetcher with rate limiting and retry logic.

Provides a robust HTTP client for fetching documentation pages with:
- Configurable rate limiting
- Automatic retry with exponential backoff
- robots.txt compliance
- Request/response logging

TODO: Implement in task F1.2
"""

from typing import Protocol

__all__ = ["Fetcher"]


class Fetcher(Protocol):
    """Protocol for HTTP fetching.

    Defines the interface that fetcher implementations must follow.
    """

    async def get(self, url: str) -> bytes:
        """Fetch URL content as bytes.

        Args:
            url: The URL to fetch.

        Returns:
            Raw bytes content of the response.
        """
        ...

    async def get_text(self, url: str) -> str:
        """Fetch URL content as text.

        Args:
            url: The URL to fetch.

        Returns:
            Text content of the response.
        """
        ...

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        ...
