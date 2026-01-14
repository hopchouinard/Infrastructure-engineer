"""
HTML to Markdown converter.

Converts HTML content to clean, readable Markdown suitable for
Claude Code consumption. Features:
- Clean extraction of main content
- Proper heading hierarchy
- Code block preservation
- Link and image handling

TODO: Implement in task F1.5
"""

from typing import Protocol

__all__ = ["HTMLConverter"]


class HTMLConverter(Protocol):
    """Protocol for HTML to Markdown conversion."""

    def convert(self, html: str, base_url: str | None = None) -> str:
        """Convert HTML content to Markdown.

        Args:
            html: Raw HTML content to convert.
            base_url: Base URL for resolving relative links.

        Returns:
            Markdown representation of the HTML content.
        """
        ...

    def extract_title(self, html: str) -> str | None:
        """Extract the title from HTML content.

        Args:
            html: Raw HTML content.

        Returns:
            The page title, or None if not found.
        """
        ...

    def extract_metadata(self, html: str) -> dict[str, str]:
        """Extract metadata from HTML content.

        Args:
            html: Raw HTML content.

        Returns:
            Dictionary of metadata (title, description, keywords, etc.).
        """
        ...
