"""
Crawl state management.

Handles persistence and recovery of crawler state, including:
- Tracking which URLs have been crawled
- Recording success/failure status for each URL
- Periodic checkpointing to disk
- Resumable crawling after interruption

TODO: Implement in task F1.7
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol

__all__ = [
    "CrawlState",
    "StateManager",
]


@dataclass
class CrawlState:
    """Represents the current state of a crawl operation.

    Attributes:
        crawled_urls: Set of URLs that have been successfully crawled.
        failed_urls: Dictionary of failed URLs to error messages.
        last_checkpoint: Timestamp of the last state save.
        total_items: Total number of items discovered.
        processed_items: Number of items processed (success or failure).

    Note:
        The last_checkpoint field uses datetime which requires custom JSON
        serialization. When implementing StateManager (F1.7), use ISO format
        strings for JSON persistence:
            - Save: dt.isoformat() if dt else None
            - Load: datetime.fromisoformat(s) if s else None
    """

    crawled_urls: set[str] = field(default_factory=set)
    failed_urls: dict[str, str] = field(default_factory=dict)
    last_checkpoint: datetime | None = None
    total_items: int = 0
    processed_items: int = 0


class StateManager(Protocol):
    """Protocol for state management.

    Defines the interface for saving and loading crawl state.
    Implementations must handle JSON serialization of datetime fields.
    """

    def load(self, path: Path) -> CrawlState:
        """Load state from disk.

        Args:
            path: Path to the state file.

        Returns:
            CrawlState instance, or empty state if file doesn't exist.
        """
        ...

    def save(self, state: CrawlState, path: Path) -> None:
        """Save state to disk.

        Args:
            state: The current crawl state.
            path: Path to save the state file.
        """
        ...

    def should_checkpoint(self, state: CrawlState, interval: int) -> bool:
        """Check if state should be checkpointed.

        Args:
            state: The current crawl state.
            interval: Number of items between checkpoints.

        Returns:
            True if a checkpoint should be saved.
        """
        ...
