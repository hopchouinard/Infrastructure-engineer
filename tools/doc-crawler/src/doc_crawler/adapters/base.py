"""
Base adapter interface for documentation sources.

All documentation source adapters must inherit from BaseAdapter and implement
the discover() and fetch() methods.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

__all__ = [
    "BaseAdapter",
    "CrawlItem",
    "CrawlResult",
]


@dataclass(frozen=True)
class CrawlItem:
    """Represents a single item to be crawled.

    Attributes:
        url: The URL of the item to crawl.
        item_type: Type of content ("article", "pdf", "page").
        metadata: Additional metadata about the item (title, category, etc.).

    Note:
        This is a frozen (immutable) dataclass. To create a modified copy,
        use dataclasses.replace().
    """

    url: str
    item_type: str  # "article", "pdf", "page"
    metadata: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def with_metadata(
        cls, url: str, item_type: str, metadata: dict[str, Any] | None = None
    ) -> "CrawlItem":
        """Create a CrawlItem with a metadata dictionary.

        Args:
            url: The URL of the item to crawl.
            item_type: Type of content ("article", "pdf", "page").
            metadata: Optional dictionary of metadata.

        Returns:
            A new CrawlItem instance.
        """
        meta_tuple = tuple(metadata.items()) if metadata else ()
        return cls(url=url, item_type=item_type, metadata=meta_tuple)

    def get_metadata(self) -> dict[str, Any]:
        """Get metadata as a dictionary.

        Returns:
            Dictionary of metadata key-value pairs.
        """
        return dict(self.metadata)


@dataclass(frozen=True)
class CrawlResult:
    """Result of crawling a single item.

    Attributes:
        url: The URL that was crawled.
        success: Whether the crawl was successful.
        content: The fetched content (str for text, bytes for binary). None on failure.
        content_type: MIME type of the content. None on failure.
        metadata: Additional metadata about the result as tuple of key-value pairs.
        error: Error message if the crawl failed.

    Note:
        This is a frozen (immutable) dataclass. When success=False, content and
        content_type will typically be None.
    """

    url: str
    success: bool
    content: str | bytes | None = None
    content_type: str | None = None
    metadata: tuple[tuple[str, Any], ...] = ()
    error: str | None = None

    @classmethod
    def success_result(
        cls,
        url: str,
        content: str | bytes,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> "CrawlResult":
        """Create a successful crawl result.

        Args:
            url: The URL that was crawled.
            content: The fetched content.
            content_type: MIME type of the content.
            metadata: Optional dictionary of metadata.

        Returns:
            A new CrawlResult indicating success.
        """
        meta_tuple = tuple(metadata.items()) if metadata else ()
        return cls(
            url=url,
            success=True,
            content=content,
            content_type=content_type,
            metadata=meta_tuple,
        )

    @classmethod
    def failure_result(
        cls,
        url: str,
        error: str,
        metadata: dict[str, Any] | None = None,
    ) -> "CrawlResult":
        """Create a failed crawl result.

        Args:
            url: The URL that was crawled.
            error: Error message describing the failure.
            metadata: Optional dictionary of metadata.

        Returns:
            A new CrawlResult indicating failure.
        """
        meta_tuple = tuple(metadata.items()) if metadata else ()
        return cls(
            url=url,
            success=False,
            error=error,
            metadata=meta_tuple,
        )

    def get_metadata(self) -> dict[str, Any]:
        """Get metadata as a dictionary.

        Returns:
            Dictionary of metadata key-value pairs.
        """
        return dict(self.metadata)


class BaseAdapter(ABC):
    """Base class for documentation source adapters.

    Each adapter is responsible for:
    1. Discovering all items to crawl from its source
    2. Fetching individual items

    Subclasses must implement the name property, discover(), and fetch() methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this adapter.

        Returns:
            A string identifier (e.g., "help_center", "guides").
        """
        ...  # pragma: no cover

    @abstractmethod
    async def discover(self) -> AsyncIterator[CrawlItem]:
        """Discover all items to crawl from this source.

        Yields:
            CrawlItem instances for each item to be crawled.
        """
        ...  # pragma: no cover
        # Type hint satisfaction for async generator - never executed
        yield CrawlItem(url="", item_type="")  # pragma: no cover

    @abstractmethod
    async def fetch(self, item: CrawlItem) -> CrawlResult:
        """Fetch a single item.

        Args:
            item: The CrawlItem to fetch.

        Returns:
            CrawlResult containing the fetched content or error information.
        """
        ...  # pragma: no cover
