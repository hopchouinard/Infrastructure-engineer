"""Tests for the Help Center adapter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from doc_crawler.adapters.base import CrawlItem
from doc_crawler.adapters.help_center import (
    HelpCenterAdapter,
    HelpCenterArticle,
    HelpCenterSection,
)
from doc_crawler.config import HelpCenterConfig
from doc_crawler.fetcher import FetchResult

# Sample HTML fixtures
CATEGORY_HTML = """
<html>
<body>
<section class="section">
  <h2 class="section-tree-title">
    <a href="/hc/en-us/sections/123-Getting-Started">Getting Started</a>
  </h2>
</section>
<section class="section">
  <h2 class="section-tree-title">
    <a href="/hc/en-us/sections/456-Advanced-Topics">Advanced Topics</a>
  </h2>
</section>
</body>
</html>
"""

SECTION_HTML = """
<html>
<body>
<ul class="article-list">
  <li class="article-list-item">
    <a href="/hc/en-us/articles/1001-First-Article">First Article</a>
  </li>
  <li class="article-list-item">
    <a href="/hc/en-us/articles/1002-Second-Article">Second Article</a>
  </li>
</ul>
</body>
</html>
"""

SECTION_WITH_PAGINATION_HTML = """
<html>
<body>
<ul class="article-list">
  <li class="article-list-item">
    <a href="/hc/en-us/articles/1001-Article">Article</a>
  </li>
</ul>
<nav class="pagination">
  <a class="pagination-next-link" href="?page=2">Next</a>
</nav>
</body>
</html>
"""

ARTICLE_HTML = """
<html>
<body>
<article class="article">
  <h1 class="article-title">How to Configure VLANs</h1>
  <section class="article-info">
    <time datetime="2024-01-15T10:30:00Z">January 15, 2024</time>
    <span class="article-author">UniFi Team</span>
  </section>
  <div class="article-body">
    <p>This article explains how to configure VLANs...</p>
    <h2>Step 1: Access Network Settings</h2>
    <p>Navigate to Settings > Networks...</p>
  </div>
</article>
</body>
</html>
"""

MINIMAL_HTML = """
<html>
<body>
<p>No specific structure here</p>
</body>
</html>
"""


class TestHelpCenterAdapter:
    """Tests for Help Center adapter."""

    @pytest.fixture
    def config(self) -> HelpCenterConfig:
        """Create test configuration."""
        return HelpCenterConfig(
            enabled=True,
            base_url="https://help.ui.com/hc/en-us",
            categories=["200320654-UniFi"],
            max_depth=3,
        )

    @pytest.fixture
    def mock_fetcher(self) -> MagicMock:
        """Create mock fetcher."""
        fetcher = MagicMock()
        fetcher.get_text = AsyncMock()
        return fetcher

    @pytest.fixture
    def adapter(
        self, config: HelpCenterConfig, mock_fetcher: MagicMock
    ) -> HelpCenterAdapter:
        """Create adapter with mock fetcher."""
        return HelpCenterAdapter(config, mock_fetcher)

    def test_name_property(self, adapter: HelpCenterAdapter) -> None:
        """Test adapter name property."""
        assert adapter.name == "help_center"

    def test_base_url_trailing_slash_removed(self, mock_fetcher: MagicMock) -> None:
        """Test that trailing slash is removed from base URL."""
        config = HelpCenterConfig(
            base_url="https://help.ui.com/hc/en-us/",
        )
        adapter = HelpCenterAdapter(config, mock_fetcher)
        assert adapter.base_url == "https://help.ui.com/hc/en-us"


class TestExtractIdFromUrl:
    """Tests for URL ID extraction."""

    @pytest.fixture
    def adapter(self) -> HelpCenterAdapter:
        """Create adapter for testing."""
        config = HelpCenterConfig()
        fetcher = MagicMock()
        return HelpCenterAdapter(config, fetcher)

    def test_extract_article_id(self, adapter: HelpCenterAdapter) -> None:
        """Test extracting ID from article URL."""
        url = "/hc/en-us/articles/123456-Some-Article"
        assert adapter._extract_id_from_url(url) == "123456"

    def test_extract_section_id(self, adapter: HelpCenterAdapter) -> None:
        """Test extracting ID from section URL."""
        url = "https://help.ui.com/hc/en-us/sections/789-Section"
        assert adapter._extract_id_from_url(url) == "789"

    def test_extract_category_id(self, adapter: HelpCenterAdapter) -> None:
        """Test extracting ID from category URL."""
        url = "/hc/en-us/categories/200320654-UniFi"
        assert adapter._extract_id_from_url(url) == "200320654"

    def test_extract_id_no_slug(self, adapter: HelpCenterAdapter) -> None:
        """Test extracting ID when no slug present."""
        # This is an edge case - should not match if no hyphen
        url = "/hc/en-us/articles/123456"
        assert adapter._extract_id_from_url(url) == ""

    def test_extract_id_no_match(self, adapter: HelpCenterAdapter) -> None:
        """Test when no ID can be extracted."""
        url = "/hc/en-us/some/other/path"
        assert adapter._extract_id_from_url(url) == ""


class TestBuildCategoryUrl:
    """Tests for category URL building."""

    @pytest.fixture
    def adapter(self) -> HelpCenterAdapter:
        """Create adapter for testing."""
        config = HelpCenterConfig(
            base_url="https://help.ui.com/hc/en-us",
        )
        fetcher = MagicMock()
        return HelpCenterAdapter(config, fetcher)

    def test_build_category_url(self, adapter: HelpCenterAdapter) -> None:
        """Test building category URL."""
        url = adapter._build_category_url("200320654-UniFi")
        assert url == "https://help.ui.com/hc/en-us/categories/200320654-UniFi"


class TestDiscoverSections:
    """Tests for section discovery."""

    @pytest.fixture
    def config(self) -> HelpCenterConfig:
        """Create test configuration."""
        return HelpCenterConfig(
            base_url="https://help.ui.com/hc/en-us",
        )

    @pytest.fixture
    def mock_fetcher(self) -> MagicMock:
        """Create mock fetcher."""
        fetcher = MagicMock()
        fetcher.get_text = AsyncMock()
        return fetcher

    @pytest.fixture
    def adapter(
        self, config: HelpCenterConfig, mock_fetcher: MagicMock
    ) -> HelpCenterAdapter:
        """Create adapter with mock fetcher."""
        return HelpCenterAdapter(config, mock_fetcher)

    @pytest.mark.asyncio
    async def test_discover_sections(
        self, adapter: HelpCenterAdapter, mock_fetcher: MagicMock
    ) -> None:
        """Test discovering sections from category page."""
        mock_fetcher.get_text.return_value = (
            CATEGORY_HTML,
            FetchResult(
                url="https://help.ui.com/hc/en-us/categories/123",
                status_code=200,
                content=b"",
                content_type="text/html",
                headers={},
                success=True,
            ),
        )

        sections = []
        async for section in adapter._discover_sections(
            "https://help.ui.com/hc/en-us/categories/123-Test"
        ):
            sections.append(section)

        assert len(sections) == 2
        assert sections[0].id == "123"
        assert sections[0].name == "Getting Started"
        assert sections[1].id == "456"
        assert sections[1].name == "Advanced Topics"

    @pytest.mark.asyncio
    async def test_discover_sections_fetch_failure(
        self, adapter: HelpCenterAdapter, mock_fetcher: MagicMock
    ) -> None:
        """Test handling fetch failure during section discovery."""
        mock_fetcher.get_text.return_value = (
            "",
            FetchResult(
                url="",
                status_code=0,
                content=b"",
                content_type="",
                headers={},
                success=False,
                error="Connection failed",
            ),
        )

        sections = []
        async for section in adapter._discover_sections("https://example.com"):
            sections.append(section)

        assert len(sections) == 0

    @pytest.mark.asyncio
    async def test_discover_sections_no_sections_found(
        self, adapter: HelpCenterAdapter, mock_fetcher: MagicMock
    ) -> None:
        """Test when no sections are found in HTML."""
        mock_fetcher.get_text.return_value = (
            MINIMAL_HTML,
            FetchResult(
                url="",
                status_code=200,
                content=b"",
                content_type="text/html",
                headers={},
                success=True,
            ),
        )

        sections = []
        async for section in adapter._discover_sections("https://example.com"):
            sections.append(section)

        assert len(sections) == 0


class TestDiscoverArticlesInSection:
    """Tests for article discovery in sections."""

    @pytest.fixture
    def config(self) -> HelpCenterConfig:
        """Create test configuration."""
        return HelpCenterConfig(
            base_url="https://help.ui.com/hc/en-us",
        )

    @pytest.fixture
    def mock_fetcher(self) -> MagicMock:
        """Create mock fetcher."""
        fetcher = MagicMock()
        fetcher.get_text = AsyncMock()
        return fetcher

    @pytest.fixture
    def adapter(
        self, config: HelpCenterConfig, mock_fetcher: MagicMock
    ) -> HelpCenterAdapter:
        """Create adapter with mock fetcher."""
        return HelpCenterAdapter(config, mock_fetcher)

    @pytest.fixture
    def section(self) -> HelpCenterSection:
        """Create test section."""
        return HelpCenterSection(
            id="123",
            name="Test Section",
            url="https://help.ui.com/hc/en-us/sections/123-Test",
            category_id="100",
        )

    @pytest.mark.asyncio
    async def test_discover_articles(
        self,
        adapter: HelpCenterAdapter,
        mock_fetcher: MagicMock,
        section: HelpCenterSection,
    ) -> None:
        """Test discovering articles in a section."""
        mock_fetcher.get_text.return_value = (
            SECTION_HTML,
            FetchResult(
                url="https://help.ui.com/hc/en-us/sections/123",
                status_code=200,
                content=b"",
                content_type="text/html",
                headers={},
                success=True,
            ),
        )

        articles = []
        async for article in adapter._discover_articles_in_section(section):
            articles.append(article)

        assert len(articles) == 2
        assert articles[0].id == "1001"
        assert articles[0].title == "First Article"
        assert articles[0].section_id == "123"
        assert articles[0].category_id == "100"
        assert articles[1].id == "1002"
        assert articles[1].title == "Second Article"

    @pytest.mark.asyncio
    async def test_discover_articles_with_pagination(
        self,
        adapter: HelpCenterAdapter,
        mock_fetcher: MagicMock,
        section: HelpCenterSection,
    ) -> None:
        """Test that pagination is followed."""
        # First page has next link, second page doesn't
        mock_fetcher.get_text.side_effect = [
            (
                SECTION_WITH_PAGINATION_HTML,
                FetchResult(
                    url="https://help.ui.com/hc/en-us/sections/123",
                    status_code=200,
                    content=b"",
                    content_type="text/html",
                    headers={},
                    success=True,
                ),
            ),
            (
                SECTION_HTML,  # Second page without pagination
                FetchResult(
                    url="https://help.ui.com/hc/en-us/sections/123?page=2",
                    status_code=200,
                    content=b"",
                    content_type="text/html",
                    headers={},
                    success=True,
                ),
            ),
        ]

        articles = []
        async for article in adapter._discover_articles_in_section(section):
            articles.append(article)

        # Should have articles from both pages (1 + 2)
        assert len(articles) == 3
        assert mock_fetcher.get_text.call_count == 2

    @pytest.mark.asyncio
    async def test_discover_articles_max_pages_limit(
        self,
        adapter: HelpCenterAdapter,
        mock_fetcher: MagicMock,
        section: HelpCenterSection,
    ) -> None:
        """Test that max_pages limit is respected."""
        # Always return pagination
        mock_fetcher.get_text.return_value = (
            SECTION_WITH_PAGINATION_HTML,
            FetchResult(
                url="",
                status_code=200,
                content=b"",
                content_type="text/html",
                headers={},
                success=True,
            ),
        )

        articles = []
        async for article in adapter._discover_articles_in_section(
            section, max_pages=3
        ):
            articles.append(article)

        # Should stop after 3 pages
        assert mock_fetcher.get_text.call_count == 3


class TestFetch:
    """Tests for article fetching."""

    @pytest.fixture
    def config(self) -> HelpCenterConfig:
        """Create test configuration."""
        return HelpCenterConfig(
            base_url="https://help.ui.com/hc/en-us",
        )

    @pytest.fixture
    def mock_fetcher(self) -> MagicMock:
        """Create mock fetcher."""
        fetcher = MagicMock()
        fetcher.get_text = AsyncMock()
        return fetcher

    @pytest.fixture
    def adapter(
        self, config: HelpCenterConfig, mock_fetcher: MagicMock
    ) -> HelpCenterAdapter:
        """Create adapter with mock fetcher."""
        return HelpCenterAdapter(config, mock_fetcher)

    @pytest.mark.asyncio
    async def test_fetch_article(
        self, adapter: HelpCenterAdapter, mock_fetcher: MagicMock
    ) -> None:
        """Test fetching article content."""
        mock_fetcher.get_text.return_value = (
            ARTICLE_HTML,
            FetchResult(
                url="https://help.ui.com/hc/en-us/articles/123",
                status_code=200,
                content=b"",
                content_type="text/html",
                headers={},
                success=True,
            ),
        )

        item = CrawlItem.with_metadata(
            url="https://help.ui.com/hc/en-us/articles/123-Test",
            item_type="article",
            metadata={"article_id": "123", "title": "Test"},
        )

        result = await adapter.fetch(item)

        assert result.success is True
        metadata = result.get_metadata()
        assert "How to Configure VLANs" in metadata.get("title", "")
        assert "2024-01-15" in metadata.get("updated_at", "")
        # Content should be from article-body
        assert result.content is not None
        assert "configure VLANs" in str(result.content)

    @pytest.mark.asyncio
    async def test_fetch_article_failure(
        self, adapter: HelpCenterAdapter, mock_fetcher: MagicMock
    ) -> None:
        """Test handling fetch failure."""
        mock_fetcher.get_text.return_value = (
            "",
            FetchResult(
                url="https://help.ui.com/hc/en-us/articles/123",
                status_code=0,
                content=b"",
                content_type="",
                headers={},
                success=False,
                error="Connection failed",
            ),
        )

        item = CrawlItem.with_metadata(
            url="https://help.ui.com/hc/en-us/articles/123",
            item_type="article",
            metadata={},
        )

        result = await adapter.fetch(item)

        assert result.success is False
        assert result.error is not None
        assert "Connection failed" in result.error

    @pytest.mark.asyncio
    async def test_fetch_handles_missing_elements(
        self, adapter: HelpCenterAdapter, mock_fetcher: MagicMock
    ) -> None:
        """Test graceful handling of missing HTML elements."""
        mock_fetcher.get_text.return_value = (
            MINIMAL_HTML,
            FetchResult(
                url="",
                status_code=200,
                content=b"",
                content_type="text/html",
                headers={},
                success=True,
            ),
        )

        item = CrawlItem.with_metadata(
            url="https://help.ui.com/hc/en-us/articles/123",
            item_type="article",
            metadata={},
        )

        result = await adapter.fetch(item)

        # Should not crash, returns content from fallback
        assert result.success is True
        assert result.content is not None


class TestDiscover:
    """Tests for full discovery flow."""

    @pytest.fixture
    def config(self) -> HelpCenterConfig:
        """Create test configuration."""
        return HelpCenterConfig(
            base_url="https://help.ui.com/hc/en-us",
            categories=["200320654-UniFi"],
        )

    @pytest.fixture
    def mock_fetcher(self) -> MagicMock:
        """Create mock fetcher."""
        fetcher = MagicMock()
        fetcher.get_text = AsyncMock()
        return fetcher

    @pytest.fixture
    def adapter(
        self, config: HelpCenterConfig, mock_fetcher: MagicMock
    ) -> HelpCenterAdapter:
        """Create adapter with mock fetcher."""
        return HelpCenterAdapter(config, mock_fetcher)

    @pytest.mark.asyncio
    async def test_discover_full_flow(
        self, adapter: HelpCenterAdapter, mock_fetcher: MagicMock
    ) -> None:
        """Test full discovery flow from category to articles."""
        # Setup mock responses for category -> sections -> articles
        mock_fetcher.get_text.side_effect = [
            # Category page
            (
                CATEGORY_HTML,
                FetchResult(
                    url="",
                    status_code=200,
                    content=b"",
                    content_type="text/html",
                    headers={},
                    success=True,
                ),
            ),
            # First section
            (
                SECTION_HTML,
                FetchResult(
                    url="",
                    status_code=200,
                    content=b"",
                    content_type="text/html",
                    headers={},
                    success=True,
                ),
            ),
            # Second section
            (
                SECTION_HTML,
                FetchResult(
                    url="",
                    status_code=200,
                    content=b"",
                    content_type="text/html",
                    headers={},
                    success=True,
                ),
            ),
        ]

        items = []
        async for item in adapter.discover():
            items.append(item)

        # Should discover articles from both sections (2 articles each)
        assert len(items) == 4
        assert all(item.item_type == "article" for item in items)

        # Check metadata is populated
        for item in items:
            metadata = item.get_metadata()
            assert "article_id" in metadata
            assert "title" in metadata
            assert metadata["source"] == "help_center"


class TestFetchArticle:
    """Tests for the fetch_article convenience method."""

    @pytest.fixture
    def config(self) -> HelpCenterConfig:
        """Create test configuration."""
        return HelpCenterConfig(
            base_url="https://help.ui.com/hc/en-us",
        )

    @pytest.fixture
    def mock_fetcher(self) -> MagicMock:
        """Create mock fetcher."""
        fetcher = MagicMock()
        fetcher.get_text = AsyncMock()
        return fetcher

    @pytest.fixture
    def adapter(
        self, config: HelpCenterConfig, mock_fetcher: MagicMock
    ) -> HelpCenterAdapter:
        """Create adapter with mock fetcher."""
        return HelpCenterAdapter(config, mock_fetcher)

    @pytest.fixture
    def article(self) -> HelpCenterArticle:
        """Create test article."""
        return HelpCenterArticle(
            id="123",
            title="Test Article",
            url="https://help.ui.com/hc/en-us/articles/123-Test",
            section_id="456",
            category_id="789",
        )

    @pytest.mark.asyncio
    async def test_fetch_article_success(
        self,
        adapter: HelpCenterAdapter,
        mock_fetcher: MagicMock,
        article: HelpCenterArticle,
    ) -> None:
        """Test successful article fetch."""
        mock_fetcher.get_text.return_value = (
            ARTICLE_HTML,
            FetchResult(
                url="",
                status_code=200,
                content=b"",
                content_type="text/html",
                headers={},
                success=True,
            ),
        )

        result = await adapter.fetch_article(article)

        assert result is not None
        assert result.article == article
        assert len(result.html_content) > 0
        assert len(result.text_content) > 0
        assert "VLANs" in result.text_content

    @pytest.mark.asyncio
    async def test_fetch_article_failure(
        self,
        adapter: HelpCenterAdapter,
        mock_fetcher: MagicMock,
        article: HelpCenterArticle,
    ) -> None:
        """Test fetch_article returns None on failure."""
        mock_fetcher.get_text.return_value = (
            "",
            FetchResult(
                url="",
                status_code=0,
                content=b"",
                content_type="",
                headers={},
                success=False,
                error="Failed",
            ),
        )

        result = await adapter.fetch_article(article)

        assert result is None


class TestHelpCenterDataModels:
    """Tests for Help Center data models."""

    def test_help_center_article_creation(self) -> None:
        """Test creating HelpCenterArticle."""
        article = HelpCenterArticle(
            id="123",
            title="Test Article",
            url="https://help.ui.com/hc/en-us/articles/123",
            section_id="456",
            category_id="789",
        )

        assert article.id == "123"
        assert article.title == "Test Article"
        assert article.author is None  # Optional field
        assert article.created_at is None
        assert article.updated_at is None

    def test_help_center_section_creation(self) -> None:
        """Test creating HelpCenterSection."""
        section = HelpCenterSection(
            id="456",
            name="Test Section",
            url="https://help.ui.com/hc/en-us/sections/456",
            category_id="789",
        )

        assert section.id == "456"
        assert section.category_id == "789"
        assert section.description is None


class TestSelectorFallbacks:
    """Tests for CSS selector fallback behavior."""

    @pytest.fixture
    def adapter(self) -> HelpCenterAdapter:
        """Create adapter for testing."""
        config = HelpCenterConfig()
        fetcher = MagicMock()
        return HelpCenterAdapter(config, fetcher)

    def test_select_first_returns_first_match(
        self, adapter: HelpCenterAdapter
    ) -> None:
        """Test that _select_first returns first matching selector's results."""
        from bs4 import BeautifulSoup

        html = '<div class="a">A</div><div class="b">B</div>'
        soup = BeautifulSoup(html, "html.parser")

        # First selector matches
        result = adapter._select_first(soup, [".a", ".b"])
        assert len(result) == 1
        assert result[0].get_text() == "A"

    def test_select_first_uses_fallback(self, adapter: HelpCenterAdapter) -> None:
        """Test that _select_first uses fallback when first doesn't match."""
        from bs4 import BeautifulSoup

        html = '<div class="b">B</div>'
        soup = BeautifulSoup(html, "html.parser")

        # First selector doesn't match, second does
        result = adapter._select_first(soup, [".a", ".b"])
        assert len(result) == 1
        assert result[0].get_text() == "B"

    def test_select_first_returns_empty_when_none_match(
        self, adapter: HelpCenterAdapter
    ) -> None:
        """Test that _select_first returns empty list when nothing matches."""
        from bs4 import BeautifulSoup

        html = '<div class="c">C</div>'
        soup = BeautifulSoup(html, "html.parser")

        result = adapter._select_first(soup, [".a", ".b"])
        assert result == []

    def test_select_one_first_returns_first_match(
        self, adapter: HelpCenterAdapter
    ) -> None:
        """Test that _select_one_first returns first matching element."""
        from bs4 import BeautifulSoup

        html = '<div class="a">A</div><div class="a">A2</div>'
        soup = BeautifulSoup(html, "html.parser")

        result = adapter._select_one_first(soup, [".a"])
        assert result is not None
        assert result.get_text() == "A"

    def test_select_one_first_returns_none_when_none_match(
        self, adapter: HelpCenterAdapter
    ) -> None:
        """Test that _select_one_first returns None when nothing matches."""
        from bs4 import BeautifulSoup

        html = '<div class="c">C</div>'
        soup = BeautifulSoup(html, "html.parser")

        result = adapter._select_one_first(soup, [".a", ".b"])
        assert result is None
