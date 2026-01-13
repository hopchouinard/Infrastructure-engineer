# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Homelab Infrastructure Engineer - an AI-powered system for managing homelab infrastructure through natural language. Uses MCP (Model Context Protocol) servers to expose network operations as tools that Claude Code can invoke.

**Goal:** Transform high-level requests like "Add my TV to a new isolated VLAN but allow it to access my NAS" into executed infrastructure changes.

**Status:** Planning/Specification Phase (no code written yet)

## Documentation Philosophy

All documentation in this project (specs, API docs, crawled vendor docs, markdown files) is written **for Claude Code consumption, not human readability**. When creating or gathering documentation:

- Optimize for structured, parseable content that an agentic AI can act upon
- Prefer explicit data formats (YAML frontmatter, tables, code blocks) over prose
- Include concrete examples, schemas, and parameter specifications
- Avoid ambiguity—state constraints, defaults, and edge cases explicitly
- Structure content for efficient retrieval (clear headings, consistent naming)

The `ai_docs/` directory is specifically designed as a knowledge corpus for Claude Code to reference when implementing features or making infrastructure changes.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Claude Code                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Slash Cmds   │    Skills    │    Hooks     │   MCP Client   │
│ /infra-*     │ (orchestr.)  │ (notify)     │                │
└──────────────┴──────────────┴──────────────┴───────┬────────┘
                                                      │
                            ┌─────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│                   SubAgent Layer                             │
├───────────────┬───────────┴───┬───────────────┬─────────────┤
│ Design Advisor│ Troubleshooter│ Security Audit│Change Planner│
└───────────────┴───────────────┴───────────────┴─────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                      MCP Server Layer                         │
├───────────────┬───────────────┬───────────────┬──────────────┤
│  unifi-mcp    │  proxmox-mcp  │    ha-mcp     │  infra-mcp   │
│  (network)    │  (vms/cts)    │  (automation) │ (dns/docker) │
└───────┬───────┴───────┬───────┴───────┬───────┴──────┬───────┘
        │               │               │              │
        ▼               ▼               ▼              ▼
    [UniFi API]    [Proxmox API]    [HA API]    [Various APIs]
```

### Key Components

| Component | Purpose |
|-----------|---------|
| **MCP Servers** | API abstraction layer; expose infrastructure as tools |
| **SubAgents** | Specialized autonomous agents for complex analysis (design, troubleshooting, security, planning) |
| **Skills** | Markdown-defined orchestration for multi-step operations (native Claude Code skill system) |
| **Slash Commands** | User-facing workflow triggers (`/infra-isolate`, `/infra-audit`) |
| **Hooks** | Event-driven validation and logging when operations execute |

## Project Structure

```
Infrastructure-engineer/
├── CLAUDE.md              # This file - project guidance
├── ai_docs/
│   └── spec/              # Detailed specifications
│       ├── masteridea.md  # Vision and architecture overview
│       ├── phase1-unifi.md        # Phase 1 overview
│       ├── phase1-f1-*.md         # Feature 1: Doc Crawler spec
│       ├── phase1-f2-*.md         # Feature 2: UniFi MCP spec
│       ├── phase1-f3-*.md         # Feature 3: Claude Integration spec
│       ├── phase1-f4-*.md         # Feature 4: SubAgent spec
│       ├── phase2-proxmox.md      # Phase 2 spec
│       ├── phase3-home-automation.md
│       ├── phase4-supporting-services.md
│       └── tasks/         # Granular task breakdowns
│           ├── phase1-f1/ # F1 tasks (10 tasks)
│           ├── phase1-f2/ # F2 tasks (11 tasks)
│           ├── phase1-f3/ # F3 tasks (7 tasks)
│           └── phase1-f4/ # F4 tasks (9 tasks)
├── scratch/               # Scratch files
└── .claude/
    └── settings.local.json    # Local permissions
```

### Planned Structure (to be created)

```
Infrastructure-engineer/
├── ai_docs/
│   ├── vendor/
│   │   └── unifi/         # Crawled UniFi documentation corpus
│   └── logs/              # Audit logs for infrastructure changes
├── mcp-servers/
│   └── unifi-mcp/         # MCP server for UniFi operations
├── tools/
│   └── doc-crawler/       # Documentation crawler utility
├── skills/                # Skill definitions (markdown)
└── .claude/
    ├── skills/            # Native Claude Code skills
    ├── commands/          # Slash command definitions
    └── hooks/             # Hook scripts
```

## Phase 1: UniFi Infrastructure (Current)

### Four Features

| Feature | Name | Location | Description |
|---------|------|----------|-------------|
| F1 | Documentation Crawler | `tools/doc-crawler/` | Crawls UniFi docs for offline use |
| F2 | UniFi MCP Server | `mcp-servers/unifi-mcp/` | Exposes UniFi API as MCP tools |
| F3 | Claude Code Integration | `.claude/` | Skills, slash commands, hooks |
| F4 | SubAgent Integration | `.claude/` | Specialized autonomous agents |

**Detailed specs:** See `ai_docs/spec/phase1-*.md` files

### MCP Tools (unifi-mcp)

**Query Tools (READ tier - auto-approved):**
`unifi_list_networks`, `unifi_get_network`, `unifi_list_clients`, `unifi_get_client`, `unifi_search_clients`, `unifi_list_devices`, `unifi_get_device`, `unifi_list_firewall_rules`, `unifi_get_firewall_rule`, `unifi_get_port_status`, `unifi_get_client_on_port`

**Config Tools (MEDIUM tier - require confirmation):**
`unifi_create_network`, `unifi_update_network`, `unifi_set_port_vlan`, `unifi_block_client`, `unifi_unblock_client`

**Config Tools (HIGH tier - explicit confirmation + rollback info):**
`unifi_delete_network`, `unifi_create_firewall_rule`, `unifi_delete_firewall_rule`, `unifi_undo`

**Config Tools (LOW tier - brief confirmation):**
`unifi_rename_client`

### SubAgents (F4)

| Agent | Purpose |
|-------|---------|
| **Design Advisor** | Network architecture consultation |
| **Troubleshooter** | Complex connectivity diagnostics |
| **Security Deep Audit** | Comprehensive security analysis |
| **Change Planner** | Multi-resource change simulation and planning |

SubAgents operate **read-only** and produce **Execution Plans** for user review.

### Slash Commands

| Command | Description |
|---------|-------------|
| `/infra-isolate` | Isolate device to own VLAN |
| `/infra-find` | Find device connection details |
| `/infra-block` | Block device from network |
| `/infra-unblock` | Unblock a blocked device |
| `/infra-status` | Show network overview |
| `/infra-undo` | Undo recent changes |
| `/security-audit` | Run security audit |
| `/infra-guest` | Create guest network |
| `/infra-unknown` | List unnamed devices |
| `/infra-rename` | Rename a device |

### Safety Model

| Tier | Operations | Behavior |
|------|-----------|----------|
| **Read** | Query, list, get | Auto-approved |
| **Low** | Rename, cosmetic | Brief confirmation |
| **Medium** | Network creation, port changes | Detailed confirmation with preview |
| **High** | Firewall rules, deletions | Explicit confirmation + rollback info |
| **Critical** | Factory reset, firmware | User-initiated only |

**Guardrails:**
- Never modify management VLAN
- Never delete network with active clients without acknowledgment
- Never create "allow all" firewall rules
- Max 5 config changes per minute
- All changes logged to audit trail

## Mandatory Documentation Rule

**CRITICAL:** Any operation that modifies, updates, deletes, or changes infrastructure is NOT complete until properly documented.

> **Authoritative Source:** See `.claude/skills/unifi-infra/SAFETY.md` for complete documentation requirements, typed block schema, and validation rules. The summary below is for quick reference only.

### Quick Reference

**Applies to:** Any operation that returns a `rollback_id` (networks, firewall rules, port config, client blocking)

**Required outputs:**
1. Change document in `ai_docs/changes/docs/{resource}-{operation}.md`
2. Index update in `ai_docs/changes/index.yaml`

**Must answer three questions:**
- What changed? (resources, operations)
- Why did it change? (intent, reasoning)
- How to undo it? (rollback IDs, procedure)

**Enforcement:** Post-change hook reminds after each configuration tool. Task is FAILED if documentation is not emitted.

For full documentation contract including typed blocks, assumptions register, and validation requirements, see `SAFETY.md`.

## Technology Stack

- **Python 3.11+**
- **MCP SDK** - Model Context Protocol (FastMCP pattern)
- **httpx** - Async HTTP client
- **Pydantic** - Data validation
- **Click** - CLI framework
- **pytest/pytest-asyncio** - Testing
- **respx** - HTTP mocking

## Development Patterns

### MCP Server Structure (FastMCP)
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("unifi-mcp")

@mcp.tool()
async def unifi_list_networks(include_default: bool = True) -> list[dict]:
    """List all networks/VLANs configured on the UniFi controller."""
    # Implementation in tools/query/networks.py
    pass
```

### Native Skill System
Skills are markdown instruction files in `.claude/skills/`:
```markdown
# unifi-infra Skill

When the user asks about network infrastructure...

## Device Isolation
To isolate a device:
1. Find the device using unifi_get_client
2. Check current VLAN assignment
3. Create new VLAN if needed using unifi_create_network
...
```

### Configuration
Credentials and settings via environment variables:
```bash
UNIFI_HOST=https://192.168.1.1
UNIFI_USERNAME=claude-api
UNIFI_PASSWORD=<secure>
UNIFI_SITE=default
```

## Key Specification Documents

| Document | Purpose |
|----------|---------|
| `ai_docs/spec/masteridea.md` | Vision, goals, full architecture |
| `ai_docs/spec/phase1-unifi.md` | Phase 1 overview, all features |
| `ai_docs/spec/phase1-f1-documentation-crawler.md` | Doc crawler design |
| `ai_docs/spec/phase1-f2-unifi-mcp-server.md` | MCP server design |
| `ai_docs/spec/phase1-f3-claude-code-integration.md` | Skills/commands/hooks |
| `ai_docs/spec/phase1-f4-subagent-integration.md` | SubAgent framework |

## Future Phases

- **Phase 2:** Proxmox integration (VMs, containers, storage)
- **Phase 3:** Home Assistant integration (automation, device control)
- **Phase 4:** Supporting services (DNS, Docker, monitoring)
