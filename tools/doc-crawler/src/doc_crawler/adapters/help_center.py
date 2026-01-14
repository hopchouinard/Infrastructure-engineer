"""
Help Center adapter for crawling help.ui.com documentation.

Handles crawling the UniFi Help Center (Zendesk-based), including:
- Category and section discovery
- Article discovery with pagination
- Article content extraction
- Metadata extraction (title, date, author)
"""

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from doc_crawler.adapters.base import BaseAdapter, CrawlItem, CrawlResult
from doc_crawler.config import HelpCenterConfig
from doc_crawler.fetcher import FetcherProtocol

__all__ = [
    "ArticleContent",
    "HelpCenterAdapter",
    "HelpCenterArticle",
    "HelpCenterCategory",
    "HelpCenterSection",
]

logger = logging.getLogger(__name__)


@dataclass
class HelpCenterCategory:
    """A Help Center category."""

    id: str
    name: str
    url: str
    description: str | None = None


@dataclass
class HelpCenterSection:
    """A Help Center section within a category."""

    id: str
    name: str
    url: str
    category_id: str
    description: str | None = None


@dataclass
class HelpCenterArticle:
    """A Help Center article."""

    id: str
    title: str
    url: str
    section_id: str
    category_id: str
    author: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class ArticleContent:
    """Full content of an article."""

    article: HelpCenterArticle
    html_content: str
    text_content: str
    metadata: dict[str, str] = field(default_factory=dict)


class HelpCenterAdapter(BaseAdapter):
    """Adapter for the UniFi Help Center (help.ui.com).

    Discovers articles by:
    1. Starting from configured category URLs
    2. Finding all sections within each category
    3. Finding all articles within each section
    4. Handling pagination for sections with many articles

    The Help Center uses Zendesk's template structure. CSS selectors
    are configured with fallbacks to handle template variations.
    """

    # CSS selectors with fallbacks for Zendesk templates
    # Updated 2024: Help Center uses latest_articles__show-more class for section links
    # Note: Selectors are ordered from most specific to least specific.
    # Avoid overly broad selectors like "a[href*='/sections/']" which could
    # match unintended links in footers, sidebars, or breadcrumbs.
    SECTION_SELECTORS = [
        "a.latest_articles__show-more[href*='/sections/']",
        "section.section .section-tree-title a",
        ".section-tree-title a",
        ".category-sections a[href*='/sections/']",
        ".section a[href*='/sections/']",
    ]

    ARTICLE_LIST_SELECTORS = [
        "a.section-article__list-name[href*='/articles/']",
        ".section-item__article a[href*='/articles/']",
        ".article-list-item a",
        "ul.article-list a",
        ".article-list a[href*='/articles/']",
    ]

    PAGINATION_SELECTORS = [
        ".pagination-next-link",
        "a[rel='next']",
        ".pagination a.next",
    ]

    ARTICLE_BODY_SELECTORS = [
        ".article-body",
        ".article-body.markdown",
        "article .content",
        ".article-content",
    ]

    ARTICLE_TITLE_SELECTORS = [
        "h1.article-title",
        ".article-header h1",
        "article h1",
    ]

    # Elements to remove before extracting content
    ELEMENTS_TO_REMOVE = [
        ".sub-nav",
        ".breadcrumbs",
        ".article-footer",
        ".article-sidebar",
        ".article-votes",
        ".article-comments",
        ".article-subscribe",
        "script",
        "style",
    ]

    def __init__(self, config: HelpCenterConfig, fetcher: FetcherProtocol) -> None:
        """Initialize the Help Center adapter.

        Args:
            config: Help Center configuration.
            fetcher: Fetcher instance (Fetcher or BrowserFetcher).
        """
        self.config = config
        self.fetcher = fetcher
        self.base_url = str(config.base_url).rstrip("/")

    @property
    def name(self) -> str:
        """Unique identifier for this adapter."""
        return "help_center"

    def _build_category_url(self, category_id: str) -> str:
        """Build URL for a category page.

        Args:
            category_id: Category ID with optional slug (e.g., "200320654-UniFi").

        Returns:
            Full category URL.
        """
        return f"{self.base_url}/categories/{category_id}"

    def _extract_id_from_url(self, url: str) -> str:
        """Extract numeric ID from a Help Center URL.

        Help Center URLs follow the pattern: /hc/en-us/{type}/{id}-{slug}
        where {id} is numeric and {slug} is the URL-friendly title.

        Args:
            url: Help Center URL (full or path only).

        Returns:
            The numeric ID, or empty string if not found.
        """
        path = urlparse(url).path
        parts = path.split("/")
        for part in parts:
            if "-" in part:
                potential_id = part.split("-")[0]
                if potential_id.isdigit():
                    return potential_id
        return ""

    def _extract_name_from_url(self, url: str) -> str:
        """Extract human-readable name from a Help Center URL slug.

        Help Center URLs follow the pattern: /hc/en-us/{type}/{id}-{slug}
        where {slug} is the URL-friendly title with hyphens.

        Args:
            url: Help Center URL (full or path only).

        Returns:
            The name extracted from slug (hyphens replaced with spaces),
            or "Unknown" if not found.
        """
        path = urlparse(url).path
        parts = path.split("/")
        for part in parts:
            if "-" in part:
                potential_id = part.split("-")[0]
                if potential_id.isdigit():
                    # Get everything after the ID
                    slug = part[len(potential_id) + 1:]  # Skip ID and hyphen
                    # Convert slug to readable name
                    return slug.replace("-", " ").title()
        return "Unknown"

    def _select_first(self, soup: BeautifulSoup, selectors: list[str]) -> list:
        """Try multiple CSS selectors and return first match.

        Args:
            soup: BeautifulSoup instance to search.
            selectors: List of CSS selectors to try in order.

        Returns:
            List of matching elements from the first successful selector,
            or empty list if none match.
        """
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return elements
        return []

    def _select_one_first(self, soup: BeautifulSoup, selectors: list[str]) -> Tag | None:
        """Try multiple CSS selectors and return first single match.

        Args:
            soup: BeautifulSoup instance to search.
            selectors: List of CSS selectors to try in order.

        Returns:
            First matching element, or None if none match.
        """
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element
        return None

    async def _fetch_and_parse(self, url: str) -> BeautifulSoup | None:
        """Fetch URL and parse as HTML.

        Args:
            url: URL to fetch.

        Returns:
            BeautifulSoup instance, or None if fetch failed.
        """
        text, result = await self.fetcher.get_text(url)
        if not result.success:
            logger.warning("Failed to fetch %s: %s", url, result.error)
            return None
        return BeautifulSoup(text, "html.parser")

    async def _discover_sections(
        self, category_url: str
    ) -> AsyncIterator[HelpCenterSection]:
        """Discover all sections in a category.

        Args:
            category_url: URL of the category page.

        Yields:
            HelpCenterSection for each section found.
        """
        soup = await self._fetch_and_parse(category_url)
        if not soup:
            return

        category_id = self._extract_id_from_url(category_url)

        # Try multiple selectors for section links
        section_links = self._select_first(soup, self.SECTION_SELECTORS)

        if not section_links:
            logger.warning(
                "No sections found at %s with selectors %s",
                category_url,
                self.SECTION_SELECTORS,
            )
            return

        # Track seen section IDs to avoid duplicates
        seen_ids: set[str] = set()

        for link in section_links:
            href = link.get("href")
            if href and "/sections/" in href:
                section_id = self._extract_id_from_url(href)
                if section_id in seen_ids:
                    continue
                seen_ids.add(section_id)

                full_url = urljoin(self.base_url, href)
                # Extract name from URL slug since link text may be "View all X"
                link_text = link.get_text(strip=True)
                if link_text.startswith("View all") or not link_text:
                    name = self._extract_name_from_url(href)
                else:
                    name = link_text

                yield HelpCenterSection(
                    id=section_id,
                    name=name,
                    url=full_url,
                    category_id=category_id,
                )

    async def _discover_articles_in_section(
        self,
        section: HelpCenterSection,
        max_pages: int = 10,
    ) -> AsyncIterator[HelpCenterArticle]:
        """Discover all articles in a section, handling pagination.

        Args:
            section: The section to discover articles from.
            max_pages: Maximum number of pages to fetch (default 10).

        Yields:
            HelpCenterArticle for each article found.
        """
        url: str | None = section.url
        pages_fetched = 0

        while url and pages_fetched < max_pages:
            soup = await self._fetch_and_parse(url)
            if not soup:
                break

            pages_fetched += 1

            # Find article links
            article_links = self._select_first(soup, self.ARTICLE_LIST_SELECTORS)

            if not article_links and pages_fetched == 1:
                logger.debug(
                    "No articles found in section %s at %s",
                    section.name,
                    url,
                )

            for link in article_links:
                href = link.get("href")
                if href and "/articles/" in href:
                    full_url = urljoin(self.base_url, href)
                    article_id = self._extract_id_from_url(href)
                    yield HelpCenterArticle(
                        id=article_id,
                        title=link.get_text(strip=True),
                        url=full_url,
                        section_id=section.id,
                        category_id=section.category_id,
                    )

            # Check for next page
            next_link = self._select_one_first(soup, self.PAGINATION_SELECTORS)
            url = urljoin(url, next_link["href"]) if next_link and next_link.get("href") else None

    async def discover(self) -> AsyncIterator[CrawlItem]:
        """Discover all articles to crawl from configured categories.

        Navigates the category -> section -> article hierarchy and
        yields a CrawlItem for each article found.

        Yields:
            CrawlItem for each article to be crawled.
        """
        for category_id in self.config.categories:
            category_url = self._build_category_url(category_id)
            logger.info("Discovering sections in category: %s", category_url)

            async for section in self._discover_sections(category_url):
                logger.debug("Discovering articles in section: %s", section.name)

                async for article in self._discover_articles_in_section(section):
                    yield CrawlItem.with_metadata(
                        url=article.url,
                        item_type="article",
                        metadata={
                            "article_id": article.id,
                            "title": article.title,
                            "section_id": article.section_id,
                            "category_id": article.category_id,
                            "source": self.name,
                        },
                    )

    async def fetch(self, item: CrawlItem) -> CrawlResult:
        """Fetch article content.

        Retrieves the article HTML, removes unwanted elements,
        extracts the article body, and enriches metadata.

        Args:
            item: The CrawlItem to fetch.

        Returns:
            CrawlResult with HTML content and extracted metadata.
        """
        text, result = await self.fetcher.get_text(item.url)

        if not result.success:
            return CrawlResult.failure_result(
                url=item.url,
                error=result.error or "Unknown error",
                metadata=item.get_metadata(),
            )

        # Parse HTML
        soup = BeautifulSoup(text, "html.parser")

        # Remove elements we don't want before extracting content
        for selector in self.ELEMENTS_TO_REMOVE:
            for elem in soup.select(selector):
                elem.decompose()

        # Extract article body
        article_body = self._select_one_first(soup, self.ARTICLE_BODY_SELECTORS)
        if article_body:
            content = str(article_body)
        else:
            # Fallback: try to get main content
            logger.warning(
                "Article body not found at %s, using fallback",
                item.url,
            )
            main = soup.select_one("article, main, .main-content")
            content = str(main) if main else text

        # Build metadata from item + extracted data
        metadata = item.get_metadata()

        # Extract title
        title_elem = self._select_one_first(soup, self.ARTICLE_TITLE_SELECTORS)
        if title_elem:
            metadata["title"] = title_elem.get_text(strip=True)

        # Extract last updated timestamp
        time_elem = soup.select_one("time[datetime]")
        if time_elem:
            metadata["updated_at"] = time_elem.get("datetime", "")

        # Extract author
        author_elem = soup.select_one(".article-author, .author-name")
        if author_elem:
            metadata["author"] = author_elem.get_text(strip=True)

        return CrawlResult.success_result(
            url=item.url,
            content=content,
            content_type="text/html",
            metadata=metadata,
        )

    async def fetch_article(self, article: HelpCenterArticle) -> ArticleContent | None:
        """Convenience method to fetch full article content.

        Creates a CrawlItem from the article, fetches it, and returns
        both HTML and plain text content.

        Args:
            article: The article to fetch.

        Returns:
            ArticleContent with HTML and text content, or None on failure.
        """
        item = CrawlItem.with_metadata(
            url=article.url,
            item_type="article",
            metadata={
                "article_id": article.id,
                "title": article.title,
                "section_id": article.section_id,
                "category_id": article.category_id,
            },
        )

        result = await self.fetch(item)
        if not result.success:
            return None

        # Extract plain text
        content = result.content
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        soup = BeautifulSoup(content, "html.parser")
        text_content = soup.get_text(separator="\n", strip=True)

        return ArticleContent(
            article=article,
            html_content=content,
            text_content=text_content,
            metadata=result.get_metadata(),
        )
