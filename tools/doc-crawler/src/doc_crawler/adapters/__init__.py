"""
Documentation source adapters.

Each adapter handles crawling a specific documentation source (Help Center, Guides, etc.).

Note:
    Only base types are exported here to avoid circular imports.
    Import concrete adapter classes directly from their modules:
        from doc_crawler.adapters.help_center import HelpCenterAdapter
        from doc_crawler.adapters.guides import GuidesAdapter
"""

from doc_crawler.adapters.base import BaseAdapter, CrawlItem, CrawlResult

__all__ = ["BaseAdapter", "CrawlItem", "CrawlResult"]
