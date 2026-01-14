"""
Help Center adapter for crawling help.ui.com documentation.

Handles crawling the UniFi Help Center, including:
- Category and article discovery
- Pagination handling
- Article content extraction

TODO: Implement in task F1.3
"""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from doc_crawler.adapters.base import BaseAdapter, CrawlItem, CrawlResult

if TYPE_CHECKING:
    from doc_crawler.config import HelpCenterConfig
    from doc_crawler.fetcher import Fetcher

__all__ = ["HelpCenterAdapter"]


class HelpCenterAdapter(BaseAdapter):
    """Adapter for the UniFi Help Center (help.ui.com).

    Crawls articles from specified categories, handling pagination
    and extracting article content.
    """

    def __init__(self, config: "HelpCenterConfig", fetcher: "Fetcher") -> None:
        """Initialize the Help Center adapter.

        Args:
            config: Help Center configuration.
            fetcher: HTTP fetcher instance.
        """
        self.config = config
        self.fetcher = fetcher

    @property
    def name(self) -> str:
        """Unique identifier for this adapter."""
        return "help_center"

    async def discover(self) -> AsyncIterator[CrawlItem]:
        """Discover all articles in configured categories.

        TODO: Implement in task F1.3
        """
        raise NotImplementedError("HelpCenterAdapter.discover() not yet implemented")
        # Type hint satisfaction for async generator - never executed
        yield CrawlItem(url="", item_type="")  # pragma: no cover

    async def fetch(self, item: CrawlItem) -> CrawlResult:
        """Fetch a single Help Center article.

        TODO: Implement in task F1.3
        """
        raise NotImplementedError("HelpCenterAdapter.fetch() not yet implemented")
