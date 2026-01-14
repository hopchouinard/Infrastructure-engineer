"""
Configuration management for the UniFi Documentation Crawler.

Supports loading configuration from:
1. Default values (sensible defaults for all settings)
2. YAML configuration file (optional)
3. Environment variables (override YAML and defaults)

Environment variables use the CRAWLER_ prefix and double underscores for nesting.
Example: CRAWLER_RATE_LIMIT__REQUESTS_PER_SECOND=2.0
"""

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "ConfigError",
    "CrawlerConfig",
    "GuidesConfig",
    "HelpCenterConfig",
    "RateLimitConfig",
    "SourcesConfig",
]


class ConfigError(Exception):
    """Configuration loading or validation error."""

    pass


class RateLimitConfig(BaseModel):
    """Rate limiting and timeout configuration."""

    requests_per_second: Annotated[float, Field(gt=0, le=100)] = 1.0
    respect_robots_txt: bool = True
    request_timeout: Annotated[float, Field(gt=0, le=300)] = 30.0
    robots_timeout: Annotated[float, Field(gt=0, le=60)] = 10.0


class HelpCenterConfig(BaseModel):
    """Help Center source configuration."""

    enabled: bool = True
    base_url: HttpUrl = HttpUrl("https://help.ui.com/hc/en-us")
    categories: list[str] = Field(default_factory=lambda: ["200320654-UniFi"])
    max_depth: Annotated[int, Field(ge=1, le=10)] = 3


class GuidesConfig(BaseModel):
    """Guides source configuration."""

    enabled: bool = True
    base_url: HttpUrl = HttpUrl("https://dl.ubnt.com/guides/UniFi/")
    file_types: list[str] = Field(default_factory=lambda: [".pdf"])


class SourcesConfig(BaseModel):
    """All documentation sources."""

    help_center: HelpCenterConfig = Field(default_factory=HelpCenterConfig)
    guides: GuidesConfig = Field(default_factory=GuidesConfig)


class CrawlerConfig(BaseSettings):
    """Main crawler configuration.

    Configuration is loaded in this order (later sources override earlier):
    1. Default values defined in this class
    2. YAML configuration file (if provided via from_yaml())
    3. Environment variables with CRAWLER_ prefix

    Example environment variables:
        CRAWLER_OUTPUT_DIR=/custom/path
        CRAWLER_RATE_LIMIT__REQUESTS_PER_SECOND=2.0
        CRAWLER_SOURCES__HELP_CENTER__ENABLED=false
    """

    model_config = SettingsConfigDict(
        env_prefix="CRAWLER_",
        env_nested_delimiter="__",
    )

    # Output
    output_dir: Path = Path("ai_docs/vendor/unifi")

    # Rate limiting
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)

    # Sources
    sources: SourcesConfig = Field(default_factory=SourcesConfig)

    # State
    state_file: str = "crawl-state.json"
    state_save_interval: Annotated[int, Field(ge=1)] = 50

    @classmethod
    def from_yaml(cls, path: Path) -> "CrawlerConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            CrawlerConfig instance with values from YAML merged with defaults.
            If the file doesn't exist, returns default configuration.

        Raises:
            ConfigError: If the YAML file exists but contains invalid YAML syntax.
        """
        import yaml

        if not path.exists():
            return cls()

        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {path}: {e}") from e

        try:
            return cls(**data)
        except Exception as e:
            raise ConfigError(f"Invalid configuration in {path}: {e}") from e
