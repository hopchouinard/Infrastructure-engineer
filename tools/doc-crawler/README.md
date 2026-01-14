# UniFi Documentation Crawler

A tool to crawl and organize UniFi documentation for offline use by Claude Code.

## Overview

This crawler fetches documentation from multiple UniFi sources and converts it to a structured markdown corpus optimized for AI consumption. The output is stored in `ai_docs/vendor/unifi/` for use by the Infrastructure Engineer project.

## Installation

```bash
# From the tools/doc-crawler directory
pip install -e ".[dev]"
```

## Usage

```bash
# Run the crawler (not yet implemented)
unifi-docs crawl

# Check status
unifi-docs status

# Show help
unifi-docs --help
```

## Configuration

Configuration can be provided via YAML file or environment variables.

### YAML Configuration

Copy `config.example.yaml` to `config.yaml` and customize:

```yaml
output_dir: "ai_docs/vendor/unifi"

rate_limit:
  requests_per_second: 1.0
  respect_robots_txt: true

sources:
  help_center:
    enabled: true
    base_url: "https://help.ui.com/hc/en-us"
    categories:
      - "200320654-UniFi"
    max_depth: 3

  guides:
    enabled: true
    base_url: "https://dl.ubnt.com/guides/UniFi/"
    file_types:
      - ".pdf"
```

### Environment Variables

Environment variables use the `CRAWLER_` prefix with double underscores for nesting:

```bash
export CRAWLER_OUTPUT_DIR=/custom/path
export CRAWLER_RATE_LIMIT__REQUESTS_PER_SECOND=2.0
export CRAWLER_SOURCES__HELP_CENTER__ENABLED=false
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Linting

```bash
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/doc_crawler/config.py
```

## Project Structure

```
src/doc_crawler/
├── __init__.py          # Package init with version
├── py.typed             # PEP 561 marker
├── config.py            # Configuration management
├── crawler.py           # Main orchestration
├── fetcher.py           # HTTP client
├── state.py             # State management
├── cli.py               # CLI entry point
├── adapters/            # Source adapters
│   ├── base.py          # Base adapter interface
│   ├── help_center.py   # Help Center adapter
│   └── guides.py        # Guides adapter
├── converters/          # Content converters
│   ├── html.py          # HTML to Markdown
│   └── pdf.py           # PDF to Markdown
└── utils/
    └── markdown.py      # Markdown utilities
```

## Implementation Status

| Component | Status | Task |
|-----------|--------|------|
| Project Setup | Complete | F1.1 |
| HTTP Fetcher | Pending | F1.2 |
| Help Center Adapter | Pending | F1.3 |
| Guides Adapter | Pending | F1.4 |
| HTML Converter | Pending | F1.5 |
| PDF Converter | Pending | F1.6 |
| State Management | Pending | F1.7 |
| CLI Interface | Pending | F1.8 |
| Integration Testing | Pending | F1.9 |
| Documentation | Pending | F1.10 |

## License

Part of the Infrastructure Engineer project.
