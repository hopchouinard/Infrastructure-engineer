"""Tests for crawler configuration."""

from pathlib import Path

import pytest
from pydantic import HttpUrl, ValidationError

from doc_crawler.config import (
    ConfigError,
    CrawlerConfig,
    GuidesConfig,
    HelpCenterConfig,
    RateLimitConfig,
    SourcesConfig,
)


class TestCrawlerConfig:
    """Tests for crawler configuration."""

    def test_default_config(self) -> None:
        """Test that default config is valid."""
        config = CrawlerConfig()

        assert config.output_dir == Path("ai_docs/vendor/unifi")
        assert config.rate_limit.requests_per_second == 1.0
        assert config.rate_limit.respect_robots_txt is True
        assert config.sources.help_center.enabled is True
        assert config.sources.guides.enabled is True

    def test_config_from_yaml(self, tmp_path: Path) -> None:
        """Test loading config from YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
output_dir: "custom/output"
rate_limit:
  requests_per_second: 2.0
""")

        config = CrawlerConfig.from_yaml(config_file)

        assert config.output_dir == Path("custom/output")
        assert config.rate_limit.requests_per_second == 2.0

    def test_config_missing_yaml(self, tmp_path: Path) -> None:
        """Test that missing YAML file returns defaults."""
        config = CrawlerConfig.from_yaml(tmp_path / "nonexistent.yaml")

        assert config.output_dir == Path("ai_docs/vendor/unifi")

    def test_config_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Test that invalid YAML syntax raises ConfigError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: : content")

        with pytest.raises(ConfigError) as exc_info:
            CrawlerConfig.from_yaml(config_file)

        assert "Invalid YAML" in str(exc_info.value)

    def test_config_invalid_values(self, tmp_path: Path) -> None:
        """Test that invalid config values raise ConfigError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
rate_limit:
  requests_per_second: -1.0
""")

        with pytest.raises(ConfigError) as exc_info:
            CrawlerConfig.from_yaml(config_file)

        assert "Invalid configuration" in str(exc_info.value)

    def test_config_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override config."""
        monkeypatch.setenv("CRAWLER_OUTPUT_DIR", "/env/override")

        config = CrawlerConfig()

        assert config.output_dir == Path("/env/override")

    def test_config_nested_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that nested environment variables override config."""
        monkeypatch.setenv("CRAWLER_RATE_LIMIT__REQUESTS_PER_SECOND", "5.0")

        config = CrawlerConfig()

        assert config.rate_limit.requests_per_second == 5.0

    def test_config_sources_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that source environment variables override config."""
        monkeypatch.setenv("CRAWLER_SOURCES__HELP_CENTER__ENABLED", "false")

        config = CrawlerConfig()

        assert config.sources.help_center.enabled is False

    def test_sources_config_defaults(self) -> None:
        """Test source configuration defaults."""
        config = CrawlerConfig()

        # Help Center - base_url is HttpUrl
        assert str(config.sources.help_center.base_url) == "https://help.ui.com/hc/en-us"
        assert "200320654-UniFi" in config.sources.help_center.categories

        # Guides - base_url is HttpUrl
        assert str(config.sources.guides.base_url) == "https://dl.ubnt.com/guides/UniFi/"
        assert ".pdf" in config.sources.guides.file_types

    def test_state_config_defaults(self) -> None:
        """Test state configuration defaults."""
        config = CrawlerConfig()

        assert config.state_file == "crawl-state.json"
        assert config.state_save_interval == 50


class TestRateLimitConfig:
    """Tests for rate limit configuration."""

    def test_default_values(self) -> None:
        """Test default rate limit values."""
        config = RateLimitConfig()

        assert config.requests_per_second == 1.0
        assert config.respect_robots_txt is True

    def test_custom_values(self) -> None:
        """Test custom rate limit values."""
        config = RateLimitConfig(
            requests_per_second=0.5,
            respect_robots_txt=False,
        )

        assert config.requests_per_second == 0.5
        assert config.respect_robots_txt is False

    def test_invalid_rate_zero(self) -> None:
        """Test that zero rate is rejected."""
        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_second=0)

    def test_invalid_rate_negative(self) -> None:
        """Test that negative rate is rejected."""
        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_second=-1.0)

    def test_invalid_rate_too_high(self) -> None:
        """Test that rate over 100 is rejected."""
        with pytest.raises(ValidationError):
            RateLimitConfig(requests_per_second=101.0)


class TestHelpCenterConfig:
    """Tests for Help Center configuration."""

    def test_default_values(self) -> None:
        """Test default Help Center values."""
        config = HelpCenterConfig()

        assert config.enabled is True
        assert str(config.base_url) == "https://help.ui.com/hc/en-us"
        assert config.max_depth == 3

    def test_invalid_max_depth_zero(self) -> None:
        """Test that zero max_depth is rejected."""
        with pytest.raises(ValidationError):
            HelpCenterConfig(max_depth=0)

    def test_invalid_max_depth_too_high(self) -> None:
        """Test that max_depth over 10 is rejected."""
        with pytest.raises(ValidationError):
            HelpCenterConfig(max_depth=11)

    def test_custom_base_url(self) -> None:
        """Test custom base URL."""
        config = HelpCenterConfig(base_url=HttpUrl("https://custom.example.com/docs"))

        assert str(config.base_url) == "https://custom.example.com/docs"


class TestGuidesConfig:
    """Tests for Guides configuration."""

    def test_default_values(self) -> None:
        """Test default Guides values."""
        config = GuidesConfig()

        assert config.enabled is True
        assert str(config.base_url) == "https://dl.ubnt.com/guides/UniFi/"
        assert ".pdf" in config.file_types


class TestSourcesConfig:
    """Tests for Sources configuration."""

    def test_default_values(self) -> None:
        """Test that both sources have defaults."""
        config = SourcesConfig()

        assert config.help_center.enabled is True
        assert config.guides.enabled is True
