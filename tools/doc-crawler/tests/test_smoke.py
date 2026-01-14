"""Smoke tests to verify basic setup."""

from dataclasses import FrozenInstanceError

import pytest


def test_imports() -> None:
    """Test that all modules can be imported."""
    from doc_crawler import (
        config,  # noqa: F401
        crawler,  # noqa: F401
        fetcher,  # noqa: F401
        state,  # noqa: F401
    )
    from doc_crawler.adapters import (
        base,  # noqa: F401
        guides,  # noqa: F401
        help_center,  # noqa: F401
    )
    from doc_crawler.converters import (
        html,  # noqa: F401
        pdf,  # noqa: F401
    )
    from doc_crawler.utils import markdown  # noqa: F401


def test_config_instantiation() -> None:
    """Test that config can be instantiated."""
    from doc_crawler.config import CrawlerConfig

    config = CrawlerConfig()
    assert config is not None


def test_base_adapter_types() -> None:
    """Test that base adapter types are properly defined."""
    from doc_crawler.adapters.base import BaseAdapter, CrawlItem, CrawlResult

    # Verify CrawlItem can be instantiated with new factory method
    item = CrawlItem.with_metadata(
        url="https://example.com",
        item_type="article",
        metadata={"title": "Test"},
    )
    assert item.url == "https://example.com"
    assert item.item_type == "article"
    assert item.get_metadata() == {"title": "Test"}

    # Verify CrawlItem is frozen (immutable)
    with pytest.raises(FrozenInstanceError):
        item.url = "https://other.com"  # type: ignore[misc]

    # Verify CrawlResult success factory
    result = CrawlResult.success_result(
        url="https://example.com",
        content="test content",
        content_type="text/html",
        metadata={"size": 100},
    )
    assert result.success is True
    assert result.content == "test content"
    assert result.get_metadata() == {"size": 100}

    # Verify CrawlResult failure factory
    failure = CrawlResult.failure_result(
        url="https://example.com",
        error="Connection timeout",
    )
    assert failure.success is False
    assert failure.content is None
    assert failure.error == "Connection timeout"

    # Verify CrawlResult is frozen (immutable)
    with pytest.raises(FrozenInstanceError):
        result.success = False  # type: ignore[misc]

    # Verify BaseAdapter is abstract
    assert hasattr(BaseAdapter, "discover")
    assert hasattr(BaseAdapter, "fetch")
    assert hasattr(BaseAdapter, "name")


def test_adapter_name_is_property() -> None:
    """Test that adapter name is an abstract property."""
    from doc_crawler.adapters.guides import GuidesAdapter
    from doc_crawler.adapters.help_center import HelpCenterAdapter

    # We can't instantiate without a fetcher, but we can check the class
    assert hasattr(HelpCenterAdapter, "name")
    assert hasattr(GuidesAdapter, "name")

    # Verify name is a property in the concrete class
    assert isinstance(
        HelpCenterAdapter.__dict__.get("name", None),
        property,
    )
    assert isinstance(
        GuidesAdapter.__dict__.get("name", None),
        property,
    )


def test_version() -> None:
    """Test that package version is defined."""
    from doc_crawler import __version__

    assert __version__ == "0.1.0"


def test_config_error_exists() -> None:
    """Test that ConfigError is available."""
    from doc_crawler.config import ConfigError

    assert issubclass(ConfigError, Exception)


def test_py_typed_marker_exists() -> None:
    """Test that py.typed marker exists for PEP 561."""
    from pathlib import Path

    from doc_crawler import __file__ as doc_crawler_file

    package_dir = Path(doc_crawler_file).parent
    py_typed = package_dir / "py.typed"
    assert py_typed.exists(), "py.typed marker missing for PEP 561 compliance"
