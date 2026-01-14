"""Pytest fixtures for the UniFi Documentation Crawler tests."""

from pathlib import Path

import pytest


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
