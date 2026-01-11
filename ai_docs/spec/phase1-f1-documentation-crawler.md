# Phase 1 - Feature 1: Documentation Crawler

A standalone utility to crawl, download, and organize UniFi documentation for offline use.

**Parent Document:** [phase1-unifi.md](./phase1-unifi.md)
**Dependencies:** None (fully independent)
**Status:** Planning

---

## 1. Purpose

### 1.1 Why This Feature

Before building automation tooling for any system, we need comprehensive documentation:
- API endpoint references
- Configuration schemas
- Behavioral documentation (what happens when X)
- Version-specific differences

This crawler creates a **local documentation corpus** that:
- Matches your exact UniFi OS/Network versions
- Is available offline
- Can be searched and indexed
- Serves as the source of truth for MCP tool implementation

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Crawl UniFi Help Center | Real-time documentation sync |
| Download official PDFs | Community forum crawling (initially) |
| HTML → Markdown conversion | Full-text search indexing |
| Local config/backup export guides | Automatic API discovery |
| Version tracking | Documentation diff/changelog |
| Incremental updates | |

### 1.3 Reusability

This crawler is designed to be **vendor-agnostic**. The same patterns can be applied to:
- Proxmox documentation (Phase 2)
- Home Assistant documentation (Phase 3)
- Any other system with web-accessible docs

---

## 2. Documentation Sources

### 2.1 Primary Sources

| Source | URL | Content Type | Priority |
|--------|-----|--------------|----------|
| UniFi Help Center | `help.ui.com/hc/en-us/categories/200320654-UniFi` | HTML articles | High |
| Official Guides | `dl.ubnt.com/guides/UniFi/` | PDF documents | High |
| UI.com Downloads | `ui.com/download/releases/` | Release notes | Medium |

### 2.2 Secondary Sources (Future)

| Source | URL | Content Type | Notes |
|--------|-----|--------------|-------|
| Community Forums | `community.ui.com` | HTML | Requires different crawl strategy |
| GitHub (unofficial) | Various repos | Markdown | API documentation efforts |
| Reddit | `r/Ubiquiti` | HTML | Troubleshooting knowledge |

### 2.3 Local Exports

In addition to crawled content, the corpus should include exports from your own UniFi console:

| Export | How to Obtain | Format | Purpose |
|--------|---------------|--------|---------|
| Settings Backup | Settings → System → Backup | `.unf` (encrypted) | Full config reference |
| Site Export | API: `GET /api/s/{site}/get/setting` | JSON | Readable config |
| Client List | Clients → Export | CSV | Current inventory |
| Network Diagram | Screenshot | PNG | Visual reference |
| API Discovery | Browser DevTools on UniFi UI | HAR/JSON | Endpoint discovery |

---

## 3. Output Structure

### 3.1 Directory Layout

```
ai_docs/vendor/unifi/
├── versions.yaml                 # Version tracking
├── crawl-state.json              # Crawler state/checkpoints
├── index.yaml                    # Crawl manifest (article metadata)
├── api/
│   ├── README.md                 # API overview
│   ├── authentication.md         # Auth flow documentation
│   ├── endpoints/
│   │   ├── clients.md            # /stat/sta, /cmd/stamgr
│   │   ├── networks.md           # /rest/networkconf
│   │   ├── firewall.md           # /rest/firewallrule
│   │   ├── devices.md            # /stat/device
│   │   └── ...
│   └── examples/
│       ├── create-vlan.json
│       ├── firewall-rule.json
│       └── ...
├── help-center/
│   ├── index.md                  # Table of contents
│   └── articles/                 # Organized by semantic topic
│       ├── vlans/                # VLAN-related articles
│       │   └── {article-slug}.md
│       ├── firewall/             # Firewall-related articles
│       │   └── {article-slug}.md
│       ├── wireless/             # Wireless-related articles
│       │   └── {article-slug}.md
│       └── general/              # Uncategorized articles
│           └── {article-slug}.md
├── guides/                       # (DEFERRED - source unavailable)
│   ├── index.md
│   ├── pdf/
│   │   └── [original PDFs]
│   └── markdown/
│       └── [converted markdown]
├── release-notes/
│   ├── network-app/
│   │   └── {version}.md
│   └── unifi-os/
│       └── {version}.md
└── local-exports/
    ├── backup-{date}.unf
    ├── site-config-{date}.json
    ├── topology-{date}.png
    └── api-discovery-{date}.har
```

### 3.2 Version Tracking

```yaml
# versions.yaml
---
# Your installed versions (update manually or via script)
installed:
  unifi_os: "4.0.21"
  network_app: "8.1.113"
  devices:
    - name: "UDM-Pro"
      model: "UDM-Pro"
      firmware: "3.2.12"
    - name: "Main Switch"
      model: "USW-24-POE"
      firmware: "6.6.61"

# Crawl metadata
crawl:
  last_run: "2025-01-09T12:00:00Z"
  sources_crawled:
    - help-center
    - guides
  articles_count: 342
  guides_count: 15

# Known API versions
api_compatibility:
  network_app_min: "7.0.0"
  network_app_max: "8.x.x"
  notes: "API changed significantly in 7.0"
```

### 3.3 Article Format

Each crawled article should be converted to markdown with frontmatter:

```markdown
---
source: help.ui.com
url: https://help.ui.com/hc/en-us/articles/123456
title: "How to Create a VLAN"
category: "UniFi Network"
crawled_at: 2025-01-09T12:00:00Z
checksum: abc123...
---

# How to Create a VLAN

[Article content converted to markdown...]
```

---

## 4. Crawler Design

### 4.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Documentation Crawler                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Fetcher   │───▶│  Converter  │───▶│   Writer    │     │
│  │  (httpx)    │    │ (html2text) │    │  (files)    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                                     │             │
│         ▼                                     ▼             │
│  ┌─────────────┐                      ┌─────────────┐      │
│  │ Rate Limiter│                      │   State     │      │
│  │ robots.txt  │                      │  Manager    │      │
│  └─────────────┘                      └─────────────┘      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Source Adapters                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Help Ctr  │ │  Guides  │ │ Releases │ │  Custom  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Components

#### Fetcher
- Async HTTP client (httpx)
- Respects `robots.txt`
- Rate limiting (configurable, default 1 req/sec)
- Retry logic with exponential backoff
- User-Agent identification

#### Source Adapters
Each documentation source has its own adapter:
- **Help Center Adapter:** Navigate category/article structure
- **Guides Adapter:** List and download PDFs from directory
- **Releases Adapter:** Parse release notes pages

#### Converter
- HTML → Markdown (using `html2text` or `markdownify`)
- PDF → Text/Markdown (using `pypdf` or `pdfplumber`)
- Preserve code blocks and tables
- Extract and save images

#### State Manager
- Track crawled URLs
- Store checksums for change detection
- Checkpoint for resumable crawls
- Incremental update support

#### Writer
- Write files to output directory
- Generate frontmatter
- Create index files
- Update `versions.yaml`

### 4.3 Crawl Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `full` | Crawl everything from scratch | Initial setup |
| `incremental` | Only new/changed content | Scheduled updates |
| `single` | Crawl specific URL/section | Testing, targeted update |
| `verify` | Check for changes without downloading | Pre-update check |

---

## 5. Technical Specification

### 5.1 Project Structure

```
tools/doc-crawler/
├── src/
│   └── doc_crawler/            # Package namespace
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── crawler.py          # Main crawler orchestration
│       ├── fetcher.py          # HTTP fetching with rate limiting
│       ├── state.py            # State management
│       ├── paths.py            # Semantic path generation
│       ├── index.py            # Index manifest generation
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── base.py         # Base adapter interface
│       │   ├── help_center.py  # UI.com Help Center
│       │   ├── guides.py       # PDF guides (DEFERRED)
│       │   └── releases.py     # Release notes
│       ├── converters/
│       │   ├── __init__.py
│       │   ├── html.py         # HTML to Markdown
│       │   └── pdf.py          # PDF to text/Markdown
│       └── utils/
│           ├── __init__.py
│           └── markdown.py     # Markdown utilities
├── tests/
│   ├── __init__.py
│   ├── test_fetcher.py
│   ├── test_adapters.py
│   └── fixtures/
│       └── [sample HTML/PDF files]
├── pyproject.toml
└── README.md
```

### 5.2 Dependencies

```toml
[project]
name = "unifi-doc-crawler"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",            # Async HTTP
    "beautifulsoup4>=4.12.0",   # HTML parsing
    "html2text>=2024.1.1",      # HTML to Markdown
    "pypdf>=4.0.0",             # PDF text extraction
    "pyyaml>=6.0.0",            # YAML config
    "click>=8.1.0",             # CLI
    "rich>=13.0.0",             # Terminal output
    "pydantic>=2.6.0",          # Data validation
    "pydantic-settings>=2.2.0", # Settings management
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",
]

[project.scripts]
unifi-docs = "doc_crawler.cli:main"
```

### 5.3 Configuration

```yaml
# config.yaml
---
output_dir: "ai_docs/vendor/unifi"

rate_limit:
  requests_per_second: 1.0
  respect_robots_txt: true

sources:
  help_center:
    enabled: true
    base_url: "https://help.ui.com/hc/en-us"
    categories:
      - "200320654-UniFi"     # Main UniFi category
    max_depth: 3

  guides:
    enabled: true
    base_url: "https://dl.ubnt.com/guides/UniFi/"
    file_types: [".pdf"]

  releases:
    enabled: false            # Enable when needed
    base_url: "https://community.ui.com/releases"

converter:
  html:
    body_width: 0             # No line wrapping
    ignore_links: false
    ignore_images: false
  pdf:
    extract_images: false     # Images from PDFs

state:
  file: "crawl-state.json"
  save_interval: 50           # Save every N pages
```

### 5.4 CLI Interface

```bash
# Full crawl
unifi-docs crawl --mode full

# Incremental update
unifi-docs crawl --mode incremental

# Crawl specific source only
unifi-docs crawl --source help-center
# Note: --source guides is disabled (source URL now redirects)

# Check for updates without downloading
unifi-docs crawl --mode verify

# Show crawl status
unifi-docs status

# Export local UniFi config (interactive guide)
unifi-docs export-local
```

---

## 6. Source Adapter Details

### 6.1 Help Center Adapter

**Discovery Strategy:**
1. Start at category page: `help.ui.com/hc/en-us/categories/200320654-UniFi`
2. Find all section links within category
3. For each section, find all article links
4. Crawl each article

**HTML Structure (current as of 2025):**
```html
<!-- Category page -->
<section class="section">
  <a href="/hc/en-us/sections/...">Section Title</a>
</section>

<!-- Section page -->
<article class="article">
  <a href="/hc/en-us/articles/...">Article Title</a>
</article>

<!-- Article page -->
<article class="article-body">
  <h1>Title</h1>
  <div class="article-body">Content...</div>
</article>
```

**Pagination:**
- Check for "next page" links
- Handle infinite scroll if present (may need JS rendering)

### 6.2 Guides Adapter

> **DEFERRED:** The `dl.ubnt.com/guides/UniFi/` directory listing now redirects to `techspecs.ui.com` (a product specifications page, not a file directory). This adapter is deferred until an alternative source is identified.

**Discovery Strategy (when available):**
1. Fetch directory listing from `dl.ubnt.com/guides/UniFi/`
2. Parse HTML for PDF links
3. Download each PDF
4. Convert to markdown (optional)

**Directory Structure:**
```html
<a href="UniFi_Dream_Machine_QSG.pdf">UniFi_Dream_Machine_QSG.pdf</a>
<a href="UniFi_Network_8_User_Guide.pdf">UniFi_Network_8_User_Guide.pdf</a>
```

### 6.3 Releases Adapter

**Strategy:**
- Parse release notes from community.ui.com/releases
- Or extract from firmware download pages
- Organize by product and version

---

## 7. Scheduling

### 7.1 Cron-Based Scheduling

For automated updates, use system cron or similar:

```bash
# Weekly crawl on Sundays at 2 AM
0 2 * * 0 /path/to/unifi-docs crawl --mode incremental >> /var/log/unifi-docs.log 2>&1
```

### 7.2 Pre-Crawl Verification

Before updating the corpus, verify changes:

```bash
# Check what would be updated
unifi-docs crawl --mode verify

# Output:
# Help Center: 12 new articles, 5 updated, 2 removed
# Guides: 1 new PDF
# Proceed with crawl? [y/N]
```

### 7.3 Post-Crawl Actions

After crawl completes:
1. Update `versions.yaml` with crawl metadata
2. Generate updated index files
3. Optionally notify (webhook, email, etc.)
4. Optionally commit to git

---

## 8. Error Handling

### 8.1 Network Errors

| Error | Handling |
|-------|----------|
| Connection timeout | Retry 3x with exponential backoff |
| 404 Not Found | Log and skip, remove from state if previously existed |
| 429 Too Many Requests | Back off, reduce rate limit |
| 5xx Server Error | Retry 3x, then skip |

### 8.2 Content Errors

| Error | Handling |
|-------|----------|
| Malformed HTML | Log warning, attempt best-effort parse |
| PDF extraction failure | Log error, keep original PDF only |
| Encoding issues | Force UTF-8, replace invalid chars |

### 8.3 State Recovery

If crawl is interrupted:
1. Load last checkpoint from `crawl-state.json`
2. Resume from last successful page
3. Re-verify partially downloaded files

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/test_adapters.py
def test_help_center_parse_category():
    html = load_fixture("help_center_category.html")
    adapter = HelpCenterAdapter(config)
    sections = adapter.parse_category(html)
    assert len(sections) > 0
    assert all(s.url.startswith("https://") for s in sections)

def test_html_to_markdown():
    html = "<h1>Title</h1><p>Content</p>"
    md = html_to_markdown(html)
    assert md == "# Title\n\nContent"
```

### 9.2 Integration Tests

- Test against live sites (sparingly, with long cache)
- Verify rate limiting actually works
- Test resume after interruption

### 9.3 Fixtures

Store sample HTML/PDF in `tests/fixtures/` for reproducible tests without network access.

---

## 10. Future Enhancements

*Not in initial scope, but possible additions:*

- [ ] Full-text search index (e.g., using SQLite FTS or MeiliSearch)
- [ ] Documentation diff/changelog between crawls
- [ ] Community forum crawling (requires different approach)
- [ ] Automatic API endpoint extraction from docs
- [ ] Integration with local UniFi controller for live schema extraction
- [ ] Web UI for browsing cached documentation

---

## 11. Interfaces

### 11.1 Output Interface (for Feature 2: MCP Server)

The MCP server will consume this documentation corpus:

```python
# How MCP server might use the corpus
class UniFiDocCorpus:
    def __init__(self, corpus_path: str):
        self.path = Path(corpus_path)

    def get_api_endpoint_doc(self, endpoint: str) -> str | None:
        """Get documentation for an API endpoint."""
        pass

    def search(self, query: str) -> list[SearchResult]:
        """Search documentation."""
        pass

    def get_version_info(self) -> VersionInfo:
        """Get installed version information."""
        pass
```

### 11.2 No External Runtime Dependencies

This crawler is a **build-time tool**, not a runtime dependency:
- Run manually or on schedule
- Produces static files
- MCP server reads files, doesn't invoke crawler

---

## 12. Open Questions

- [ ] Should PDF conversion be mandatory or optional?
- [ ] Include images from articles or text only?
- [ ] How to handle articles requiring login (if any)?
- [ ] Should we version-control the corpus (git)?
- [ ] Cache duration before re-checking for updates?

---

## 13. Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| F1.1 | Project setup | Directory structure, dependencies, config |
| F1.2 | Fetcher implementation | HTTP client with rate limiting |
| F1.3 | Help Center adapter | Crawl help.ui.com |
| F1.4 | Guides adapter | **DEFERRED** - `dl.ubnt.com/guides/UniFi/` now redirects |
| F1.5 | HTML converter | HTML → Markdown |
| F1.6 | PDF converter | PDF → text extraction |
| F1.7 | State management | Incremental crawl support, index generation |
| F1.8 | CLI interface | Command-line tool |
| F1.9 | Integration Testing | Unit and integration tests |
| F1.10 | Documentation | README and usage guide |

---

*Document Version: 1.1*
*Last Updated: 2025-01-10*
