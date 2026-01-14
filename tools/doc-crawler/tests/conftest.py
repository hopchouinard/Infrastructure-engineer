"""Pytest fixtures for the UniFi Documentation Crawler tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
import respx
from respx import MockRouter


@pytest.fixture
def sample_config_yaml(tmp_path: Path) -> Path:
    """Create a sample configuration YAML file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
output_dir: "test/output"
rate_limit:
  requests_per_second: 2.0
  respect_robots_txt: true
sources:
  help_center:
    enabled: true
    base_url: "https://help.ui.com/hc/en-us"
    categories:
      - "200320654-UniFi"
  guides:
    enabled: false
""")
    return config_file


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def respx_mock() -> Generator[MockRouter, None, None]:
    """Provide a respx mock router for HTTP mocking.

    Usage:
        def test_fetch(respx_mock):
            respx_mock.get("https://example.com").respond(status_code=200)
            # ... test code ...
    """
    with respx.mock(assert_all_called=False) as mock:
        yield mock
