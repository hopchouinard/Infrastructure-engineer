"""
Guides adapter for crawling dl.ubnt.com documentation.

Handles crawling the UniFi Guides directory, including:
- Directory listing and PDF discovery
- File type filtering
- PDF download handling

TODO: Implement in task F1.4
"""

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

from doc_crawler.adapters.base import BaseAdapter, CrawlItem, CrawlResult

if TYPE_CHECKING:
    from doc_crawler.config import GuidesConfig
    from doc_crawler.fetcher import Fetcher

__all__ = ["GuidesAdapter"]


class GuidesAdapter(BaseAdapter):
    """Adapter for UniFi Guides (dl.ubnt.com/guides/UniFi/).

    Crawls PDF guides and documentation from the Ubiquiti
    downloads directory.
    """

    def __init__(self, config: "GuidesConfig", fetcher: "Fetcher") -> None:
        """Initialize the Guides adapter.

        Args:
            config: Guides configuration.
            fetcher: HTTP fetcher instance.
        """
        self.config = config
        self.fetcher = fetcher

    @property
    def name(self) -> str:
        """Unique identifier for this adapter."""
        return "guides"

    async def discover(self) -> AsyncIterator[CrawlItem]:
        """Discover all PDF guides in the directory.

        TODO: Implement in task F1.4
        """
        raise NotImplementedError("GuidesAdapter.discover() not yet implemented")
        # Type hint satisfaction for async generator - never executed
        yield CrawlItem(url="", item_type="")  # pragma: no cover

    async def fetch(self, item: CrawlItem) -> CrawlResult:
        """Fetch a single guide file.

        TODO: Implement in task F1.4
        """
        raise NotImplementedError("GuidesAdapter.fetch() not yet implemented")
