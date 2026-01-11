# Homelab Infrastructure Engineer

An AI-powered system for managing homelab infrastructure through natural language, built on Claude Code and the Model Context Protocol (MCP).

## Overview

Transform high-level requests into executed infrastructure changes:

> "Add my TV to a new isolated VLAN but allow it to access my NAS"

The system decomposes this into:
1. Create a new VLAN (e.g., VLAN 40 "IoT-Media")
2. Configure switch port tagging for the TV's physical port
3. Create firewall rules allowing TV → NAS on required ports
4. Deny all other inter-VLAN traffic from the new VLAN

All with appropriate safety confirmations and full audit logging.

## Current Status

**Phase 1: Planning/Specification** - Detailed specifications complete, implementation pending.

| Component | Status |
|-----------|--------|
| Specifications | Complete |
| Documentation Crawler (F1) | Not started |
| UniFi MCP Server (F2) | Not started |
| Claude Code Integration (F3) | Not started |
| SubAgent Integration (F4) | Not started |

## Features

### Phase 1: UniFi Network Management

- **Query Operations** - List networks, clients, devices, firewall rules, port status
- **Configuration Operations** - Create/delete VLANs, manage firewall rules, configure ports, block clients
- **Safety System** - Tiered confirmations, guardrails against dangerous operations, rollback support
- **Audit Logging** - Complete trail of all infrastructure changes

### Intelligent Agents

| Agent | Purpose |
|-------|---------|
| **Design Advisor** | Network architecture consultation and recommendations |
| **Troubleshooter** | Complex connectivity issue diagnosis |
| **Security Auditor** | Comprehensive security analysis and vulnerability detection |
| **Change Planner** | Multi-resource change simulation and planning |

### User Interface

Natural language commands through Claude Code:

```
/infra-isolate    - Isolate a device to its own VLAN
/infra-find       - Find where a device is connected
/infra-block      - Block a device from the network
/infra-status     - Show network overview
/security-audit   - Run comprehensive security audit
/infra-undo       - Undo recent changes
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Claude Code                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Slash Cmds   │    Skills    │    Hooks     │   MCP Client   │
└──────────────┴──────────────┴──────────────┴───────┬────────┘
                                                      │
┌─────────────────────────────────────────────────────┴────────┐
│                      SubAgent Layer                           │
├───────────────┬───────────────┬───────────────┬──────────────┤
│ Design Advisor│ Troubleshooter│ Security Audit│Change Planner│
└───────────────┴───────────────┴───────────────┴──────────────┘
                                  │
┌─────────────────────────────────┴────────────────────────────┐
│                      MCP Server Layer                         │
├───────────────┬───────────────┬───────────────┬──────────────┤
│  unifi-mcp    │  proxmox-mcp  │    ha-mcp     │  infra-mcp   │
│  (Phase 1)    │  (Phase 2)    │  (Phase 3)    │  (Phase 4)   │
└───────────────┴───────────────┴───────────────┴──────────────┘
```

### How It Works

1. **MCP Servers** wrap infrastructure APIs (UniFi, Proxmox, Home Assistant) as tools
2. **Skills** define multi-step workflows that chain tools together
3. **SubAgents** handle complex analysis requiring investigation and reasoning
4. **Hooks** provide validation and logging at operation boundaries
5. **Slash Commands** give users explicit workflow triggers

## Safety Model

All operations are categorized by risk level:

| Tier | Examples | Behavior |
|------|----------|----------|
| **Read** | List clients, query status | Auto-approved |
| **Low** | Rename client | Brief confirmation |
| **Medium** | Create VLAN, configure port | Detailed preview + confirmation |
| **High** | Create firewall rule, delete VLAN | Explicit confirmation + rollback info |
| **Critical** | Factory reset, firmware update | User-initiated only |

### Guardrails

- Management VLAN is protected from modification
- Cannot delete VLANs with active clients without explicit acknowledgment
- "Allow all" firewall rules are blocked
- Rate limited to 5 configuration changes per minute
- All changes logged with rollback data

## Project Structure

```
Infrastructure-engineer/
├── README.md                 # This file
├── CLAUDE.md                 # Claude Code guidance
├── ai_docs/
│   └── spec/                 # Detailed specifications
│       ├── masteridea.md     # Vision and architecture
│       ├── phase1-unifi.md   # Phase 1 overview
│       ├── phase1-f1-*.md    # Feature specs
│       ├── phase1-f2-*.md
│       ├── phase1-f3-*.md
│       ├── phase1-f4-*.md
│       └── tasks/            # Granular implementation tasks
│           ├── phase1-f1/    # 10 tasks
│           ├── phase1-f2/    # 11 tasks
│           ├── phase1-f3/    # 7 tasks
│           └── phase1-f4/    # 9 tasks
└── .claude/
    └── settings.local.json   # Local permissions
```

### Planned Structure

```
Infrastructure-engineer/
├── mcp-servers/
│   └── unifi-mcp/            # UniFi MCP server
│       ├── src/unifi_mcp/
│       │   ├── server.py     # FastMCP server
│       │   ├── client/       # UniFi API client
│       │   ├── tools/        # Tool implementations
│       │   ├── safety/       # Validation & rollback
│       │   └── logging/      # Audit logging
│       └── tests/
├── tools/
│   └── doc-crawler/          # Documentation crawler
├── ai_docs/
│   ├── vendor/unifi/         # Crawled documentation
│   └── logs/                 # Audit logs
└── .claude/
    ├── skills/               # Skill definitions
    ├── commands/             # Slash commands
    └── hooks/                # Hook scripts
```

## Technology Stack

- **Python 3.11+** - Primary language
- **MCP SDK** - Model Context Protocol implementation
- **httpx** - Async HTTP client for API calls
- **Pydantic** - Data validation and settings
- **Click** - CLI framework
- **pytest** - Testing framework
- **respx** - HTTP mocking for tests

## Roadmap

### Phase 1: UniFi Infrastructure (Current)
- Documentation crawler for offline UniFi docs
- MCP server exposing UniFi Network API
- Claude Code skills, commands, and hooks
- SubAgents for complex analysis

### Phase 2: Proxmox Integration
- VM and container lifecycle management
- Storage management
- Backup operations
- Network bridge configuration

### Phase 3: Home Automation
- Home Assistant API integration
- Device control and automation
- Scene management
- Presence detection via UniFi clients

### Phase 4: Supporting Services
- DNS management (Pi-hole, AdGuard)
- Docker container management
- Monitoring integration (Grafana, Prometheus)
- Certificate management

### Cross-System Orchestration
Once multiple MCP servers exist:
- "Spin up a new VM, assign it to the IoT VLAN, and add it to Home Assistant"
- "When guest WiFi client connects, create temporary container for isolated browsing"

## Prerequisites

### UniFi Setup

1. **UniFi Hardware**: UDM, UDM-Pro, UDM-SE, or Cloud Key + UniFi devices
2. **API User**: Create a dedicated local admin user for API access
3. **Network Access**: Claude Code must be able to reach the UniFi controller

### Development Environment

- Python 3.11+
- Claude Code CLI
- Access to UniFi controller for integration testing

## Getting Started

*Implementation pending. Check back after Phase 1 development begins.*

```bash
# Clone the repository
git clone https://github.com/hopchouinard/Infrastructure-engineer.git
cd Infrastructure-engineer

# Review specifications
cat ai_docs/spec/masteridea.md
cat ai_docs/spec/phase1-unifi.md

# Start with Feature 1 (Documentation Crawler)
cat ai_docs/spec/phase1-f1-documentation-crawler.md
```

## Documentation

All specifications are in `ai_docs/spec/`:

| Document | Description |
|----------|-------------|
| `masteridea.md` | Vision, goals, complete architecture |
| `phase1-unifi.md` | Phase 1 overview with all features |
| `phase1-f1-documentation-crawler.md` | Doc crawler specification |
| `phase1-f2-unifi-mcp-server.md` | MCP server specification |
| `phase1-f3-claude-code-integration.md` | Skills/commands/hooks spec |
| `phase1-f4-subagent-integration.md` | SubAgent framework spec |
| `phase2-proxmox.md` | Proxmox integration planning |
| `phase3-home-automation.md` | Home Assistant planning |
| `phase4-supporting-services.md` | Supporting services planning |

Task breakdowns are in `ai_docs/spec/tasks/phase1-f*/`.

## Contributing

This project is in early development. Contributions welcome after initial implementation is complete.

## License

*License TBD*

---

**Note**: This project is designed for personal homelab use. The specifications prioritize safety and reversibility, but you should always have backups and understand the changes being made to your infrastructure.
