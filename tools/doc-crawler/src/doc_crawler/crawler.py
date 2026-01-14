"""
Main crawler orchestration.

Coordinates the crawling process across all enabled sources, managing:
- Source adapter initialization
- Concurrent crawling with rate limiting
- Progress tracking and state persistence
- Error handling and retry logic

TODO: Implement in tasks F1.2-F1.7
"""

from typing import TYPE_CHECKING

__all__ = ["Crawler"]

if TYPE_CHECKING:
    from doc_crawler.config import CrawlerConfig


class Crawler:
    """Main crawler orchestrator.

    Coordinates crawling across multiple documentation sources,
    handling rate limiting, state persistence, and error recovery.
    """

    def __init__(self, config: "CrawlerConfig") -> None:
        """Initialize the crawler with configuration.

        Args:
            config: Crawler configuration instance.
        """
        self.config = config

    async def run(self) -> None:
        """Run the crawler.

        TODO: Implement in task F1.7 (State Management integration)
        """
        raise NotImplementedError("Crawler.run() not yet implemented")
