# Phase 2: Proxmox Integration

Detailed specification for building the Proxmox MCP server and VM/container management tooling.

**Parent Document:** [masteridea.md](./masteridea.md)
**Prerequisite:** Phase 1 (UniFi) complete
**Status:** Planning - Awaiting Research
**Target Hardware:** Proxmox VE Node(s) + Storage

---

## Features Overview

Phase 2 consists of four features:

| Feature | Name | Spec Document | Description |
|---------|------|---------------|-------------|
| F1 | Documentation & Research | [phase2-f1-documentation-research.md](./phase2-f1-documentation-research.md) | Gathers Proxmox API docs and establishes project foundation |
| F2 | Proxmox MCP Server | [phase2-f2-proxmox-mcp-server.md](./phase2-f2-proxmox-mcp-server.md) | Exposes Proxmox API as MCP tools |
| F3 | Claude Code Integration | [phase2-f3-claude-code-integration.md](./phase2-f3-claude-code-integration.md) | Skills, slash commands, hooks |
| F4 | SubAgent Integration | [phase2-f4-subagent-integration.md](./phase2-f4-subagent-integration.md) | Specialized autonomous agents for VM/container analysis |

**See individual feature specifications for detailed requirements.**

---

## 1. Prerequisites

### 1.1 Hardware/Software Inventory

Before implementation, document your Proxmox ecosystem:

```yaml
# To be filled in during research phase
proxmox:
  host: ""              # e.g., 192.168.1.10
  version: ""           # e.g., 8.1
  kernel: ""
  cluster_name: ""      # If clustered

nodes:
  - name: ""
    ip: ""
    cpu_cores: 0
    ram_gb: 0
    role: ""            # master, member

storage:
  - name: ""
    type: ""            # local, nfs, zfs, ceph, etc.
    size: ""
    shared: false       # Available across cluster

network_bridges:
  - name: ""            # e.g., vmbr0
    vlan_aware: false
    ports: []
    comment: ""
```

### 1.2 API Access Setup

**Step 1: Create API token**
```
Datacenter → Permissions → API Tokens → Add
- User: root@pam (or dedicated user)
- Token ID: claude-api
- Privilege Separation: Yes/No (TBD based on needs)
```

**Step 2: Document token**
```
Token: root@pam!claude-api
Secret: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

**Step 3: Verify access**
```bash
curl -k -H "Authorization: PVEAPIToken=root@pam!claude-api=SECRET" \
  https://{PROXMOX_HOST}:8006/api2/json/version
```

**Step 4: Discover API endpoints**
- Use Proxmox API documentation
- Test endpoints against your version
- Note any version-specific differences

### 1.3 Resource Baseline

Document current virtualization state before making any changes:

| Item | Current Value | Notes |
|------|---------------|-------|
| Total VMs | | Baseline count |
| Total Containers | | LXC count |
| Storage pools | | Names and types |
| Reserved VM IDs | | For automation |
| Template IDs | | Available templates |
| Backup schedule | | Current configuration |

---

## 2. Documentation Corpus

### 2.1 Documentation Sources

| Source | URL Pattern | Content Type | Priority |
|--------|-------------|--------------|----------|
| Official API Docs | `pve.proxmox.com/pve-docs/api-viewer/` | HTML/JSON | High |
| Wiki | `pve.proxmox.com/wiki/*` | HTML | High |
| proxmoxer Docs | `proxmoxer.github.io/docs/` | HTML | High |
| Community Forums | `forum.proxmox.com/*` | HTML | Medium |

### 2.2 Local Exports

From your Proxmox node, export:

| Export | Command/Location | Format | Purpose |
|--------|------------------|--------|---------|
| Node config | `/etc/pve/` | Various | Configuration reference |
| VM inventory | `qm list` | Text | Current VM list |
| Container inventory | `pct list` | Text | Current CT list |
| Storage config | `pvesm status` | Text | Storage overview |

### 2.3 Output Structure

```
ai_docs/vendor/proxmox/
├── versions.yaml           # Version tracking
├── api/
│   ├── endpoints.md        # Discovered endpoints
│   ├── authentication.md   # Auth flow documentation
│   ├── vms.md              # VM management API
│   ├── containers.md       # LXC API
│   ├── storage.md          # Storage API
│   ├── backup.md           # Backup/restore API
│   ├── cluster.md          # Cluster operations
│   └── examples/           # Request/response examples
├── wiki/
│   └── [relevant articles as markdown]
└── local-exports/
    ├── pve-config-YYYY-MM-DD/
    ├── vm-inventory.txt
    └── storage-status.txt
```

---

## 3. MCP Server: `proxmox-mcp`

### 3.1 Project Structure

See [phase2-f2-proxmox-mcp-server.md](./phase2-f2-proxmox-mcp-server.md) for the detailed project structure.

**Key points:**
- Uses **FastMCP pattern** with `@mcp.tool()` decorators for tool registration
- Tools defined inline in `server.py`, logic in `tools/query/` and `tools/config/` subdirectories
- Separate `safety/` module for validation, rate limiting, and rollback
- Comprehensive test fixtures in `tests/fixtures/api_responses/`

```
mcp-servers/proxmox-mcp/
├── src/proxmox_mcp/
│   ├── server.py               # MCP server with FastMCP
│   ├── config.py               # Configuration management
│   ├── client/                 # Proxmox API client
│   ├── tools/                  # Tool implementations
│   │   ├── query/              # Query tool functions
│   │   └── config/             # Config tool functions
│   ├── models/                 # Data models
│   │   ├── vm.py
│   │   ├── container.py
│   │   └── storage.py
│   ├── safety/                 # Validation, tiers, rollback
│   └── logging/                # Audit logging
├── tests/
│   └── fixtures/
│       └── api_responses/
├── pyproject.toml
└── README.md
```

### 3.2 Dependencies

```toml
[project]
name = "proxmox-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",              # MCP SDK
    "proxmoxer>=2.0.0",        # Proxmox API client
    "httpx>=0.27.0",           # Async HTTP client
    "pydantic>=2.0.0",         # Data validation
    "python-dotenv>=1.0.0",    # Environment variables
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",           # HTTP mocking
]
```

### 3.3 Configuration

```python
# src/config.py
from pydantic_settings import BaseSettings

class ProxmoxConfig(BaseSettings):
    """Configuration loaded from environment."""

    proxmox_host: str                  # https://192.168.1.10:8006
    proxmox_token_id: str              # root@pam!claude-api
    proxmox_token_secret: str          # (from secure store)
    proxmox_verify_ssl: bool = False   # Self-signed certs
    proxmox_node: str = ""             # Default node (if single-node)

    # Safety settings
    dry_run: bool = False              # Preview mode
    require_confirmation: bool = True  # For config changes
    max_changes_per_minute: int = 5    # Rate limit

    # Logging
    audit_log_path: str = "ai_docs/logs/infra-changes.log"

    class Config:
        env_file = ".env"
```

---

## 4. Tool Specifications

### 4.1 Query Tools (Auto-Approved)

| Tool | Description |
|------|-------------|
| `proxmox_list_nodes` | List all nodes in cluster |
| `proxmox_get_node_status` | Node resource usage |
| `proxmox_list_vms` | List all VMs with status |
| `proxmox_get_vm` | Get detailed VM info |
| `proxmox_list_containers` | List all LXC containers |
| `proxmox_get_container` | Get detailed container info |
| `proxmox_list_storage` | List storage pools |
| `proxmox_get_storage` | Get storage details |
| `proxmox_list_backups` | List available backups |
| `proxmox_list_templates` | List VM/CT templates |
| `proxmox_get_task_status` | Get async task status |

### 4.2 VM Management Tools (Require Confirmation)

| Tool | Description | Risk |
|------|-------------|------|
| `proxmox_create_vm` | Create new VM | Medium |
| `proxmox_clone_vm` | Clone VM or template | Medium |
| `proxmox_start_vm` | Start VM | Low |
| `proxmox_stop_vm` | Stop VM (graceful ACPI) | Low |
| `proxmox_shutdown_vm` | Force shutdown | Medium |
| `proxmox_reset_vm` | Hard reset | Medium |
| `proxmox_delete_vm` | Delete VM | High |
| `proxmox_snapshot_vm` | Create snapshot | Low |
| `proxmox_rollback_vm` | Rollback to snapshot | High |
| `proxmox_delete_snapshot` | Delete snapshot | Medium |
| `proxmox_migrate_vm` | Migrate to another node | High |
| `proxmox_update_vm_config` | Modify VM settings | Medium |

### 4.3 Container Management Tools (Require Confirmation)

| Tool | Description | Risk |
|------|-------------|------|
| `proxmox_create_container` | Create LXC | Medium |
| `proxmox_clone_container` | Clone container | Medium |
| `proxmox_start_container` | Start LXC | Low |
| `proxmox_stop_container` | Stop LXC | Low |
| `proxmox_shutdown_container` | Force shutdown | Medium |
| `proxmox_delete_container` | Delete LXC | High |
| `proxmox_snapshot_container` | Create snapshot | Low |
| `proxmox_rollback_container` | Rollback to snapshot | High |

### 4.4 Storage Tools

| Tool | Description | Risk |
|------|-------------|------|
| `proxmox_list_volumes` | List volumes in storage | Read |
| `proxmox_create_volume` | Create disk/volume | Medium |
| `proxmox_delete_volume` | Delete volume | High |
| `proxmox_resize_volume` | Resize disk | Medium |
| `proxmox_move_volume` | Move to different storage | Medium |

### 4.5 Backup Tools

| Tool | Description | Risk |
|------|-------------|------|
| `proxmox_backup_vm` | Backup VM | Low |
| `proxmox_backup_container` | Backup container | Low |
| `proxmox_restore_backup` | Restore from backup | High |
| `proxmox_delete_backup` | Delete backup | Medium |
| `proxmox_list_backup_jobs` | List scheduled jobs | Read |

### 4.6 Complete Tool Summary

| Category | Tools |
|----------|-------|
| **Query (READ)** | `proxmox_list_nodes`, `proxmox_get_node_status`, `proxmox_list_vms`, `proxmox_get_vm`, `proxmox_list_containers`, `proxmox_get_container`, `proxmox_list_storage`, `proxmox_get_storage`, `proxmox_list_backups`, `proxmox_list_templates`, `proxmox_get_task_status` |
| **Config (LOW)** | `proxmox_start_vm`, `proxmox_stop_vm`, `proxmox_start_container`, `proxmox_stop_container`, `proxmox_snapshot_vm`, `proxmox_snapshot_container`, `proxmox_backup_vm`, `proxmox_backup_container` |
| **Config (MEDIUM)** | `proxmox_create_vm`, `proxmox_clone_vm`, `proxmox_create_container`, `proxmox_clone_container`, `proxmox_shutdown_vm`, `proxmox_reset_vm`, `proxmox_shutdown_container`, `proxmox_create_volume`, `proxmox_resize_volume`, `proxmox_move_volume`, `proxmox_delete_snapshot`, `proxmox_delete_backup`, `proxmox_update_vm_config` |
| **Config (HIGH)** | `proxmox_delete_vm`, `proxmox_delete_container`, `proxmox_rollback_vm`, `proxmox_rollback_container`, `proxmox_delete_volume`, `proxmox_restore_backup`, `proxmox_migrate_vm`, `proxmox_undo` |

---

## 5. Orchestration Layer

This section provides a high-level overview. See feature specifications for detailed implementations:
- **Feature 3:** [phase2-f3-claude-code-integration.md](./phase2-f3-claude-code-integration.md) - Skills, Commands, Hooks
- **Feature 4:** [phase2-f4-subagent-integration.md](./phase2-f4-subagent-integration.md) - SubAgents for complex analysis

### 5.1 Native Skill System

Skills use **Claude Code's native skill system** - markdown instruction files in `.claude/skills/` that Claude follows when activated.

**Core Skills:**
| Skill | Purpose |
|-------|---------|
| `proxmox-infra` | Core VM/container management (create, snapshot, lifecycle) |
| `vm-provisioning` | VM creation from templates with networking |
| `backup-recovery` | Backup management and restoration workflows |

### 5.2 Slash Commands

Commands in `.claude/commands/` provide explicit, user-invoked workflows:

| Command | Description |
|---------|-------------|
| `/vm-create` | Create VM from template |
| `/vm-snapshot` | Snapshot VM before changes |
| `/vm-restore` | Restore VM from backup/snapshot |
| `/vm-migrate` | Migrate VM to another node |
| `/ct-create` | Create container from template |
| `/pve-status` | Show cluster/node overview |
| `/pve-backup` | Trigger backup job |
| `/pve-undo` | Undo recent changes |

### 5.3 SubAgents (Feature 4)

Specialized autonomous agents for complex analysis tasks:

| Agent | Purpose |
|-------|---------|
| **Capacity Planner** | Resource allocation and capacity analysis |
| **Migration Advisor** | VM/CT migration planning |
| **Backup Auditor** | Backup coverage and retention analysis |
| **Performance Analyzer** | Resource utilization diagnostics |

SubAgents operate read-only and produce **Execution Plans** for user review.

### 5.4 Hooks

Event-driven shell scripts in `.claude/hooks/` for validation and logging:

| Hook | Purpose |
|------|---------|
| `pre-delete-vm.sh` | Confirms backup exists before VM deletion |
| `pre-migrate.sh` | Validates target node capacity |
| `post-change-log.sh` | Logs configuration changes |

---

## 6. Cross-System Integration

### 6.1 UniFi + Proxmox

| Scenario | Integration |
|----------|-------------|
| New VM needs network | Query UniFi for available VLANs, configure VM bridge |
| VM on specific VLAN | Create VLAN-tagged bridge in Proxmox matching UniFi VLAN |
| Network isolation | Coordinate firewall rules in UniFi with VM placement |

### 6.2 Shared Orchestration Example

**"Create isolated dev environment":**
1. (UniFi) Create VLAN 50 "Dev-Environment"
2. (UniFi) Firewall: Allow VLAN 50 → Internet, block → LAN
3. (Proxmox) Create VM on bridge tagged to VLAN 50
4. Report complete isolated environment

---

## 7. Safety Model

### 7.1 Permission Tiers

| Tier | Operations | Behavior |
|------|-----------|----------|
| **Read** | Query, list, get | Auto-approved |
| **Low** | Start, stop, snapshot | Brief confirmation |
| **Medium** | Create, clone, resize | Detailed confirmation with preview |
| **High** | Delete, rollback, migrate | Explicit confirmation + rollback info |
| **Critical** | Cluster operations | User-initiated only |

### 7.2 Guardrails

- Never delete VM/CT with running state without stop first
- Always snapshot before destructive operations
- Verify backup exists before deletion
- Max 5 config changes per minute
- All changes logged to audit trail
- Prevent deletion of last backup

---

## 8. Testing Strategy

### 8.1 Unit Tests

Mock Proxmox API responses for all tool tests:

```python
# tests/test_tools_query.py
import pytest
from respx import MockRouter

@pytest.fixture
def mock_proxmox(respx_mock: MockRouter):
    respx_mock.get("/api2/json/nodes").respond(json={
        "data": [
            {"node": "pve", "status": "online", ...}
        ]
    })
    return respx_mock

async def test_list_nodes(mock_proxmox, proxmox_client):
    nodes = await proxmox_client.list_nodes()
    assert len(nodes) == 1
    assert nodes[0].name == "pve"
```

### 8.2 Integration Tests

Run against real Proxmox in controlled conditions.

### 8.3 Dry Run Mode

All config tools support `dry_run=True`.

---

## 9. Milestones

Phase 2 milestones are tracked at the feature level. See individual specifications for detailed task breakdowns.

### Feature 1: Documentation & Research
| ID | Milestone |
|----|-----------|
| F1.1 | Project setup |
| F1.2 | API documentation gathering |
| F1.3 | Local environment documentation |
| F1.4 | Version compatibility notes |

### Feature 2: Proxmox MCP Server
| ID | Milestone |
|----|-----------|
| F2.1 | Project setup |
| F2.2 | Configuration management |
| F2.3 | API client with authentication |
| F2.4 | Query tools implemented |
| F2.5 | VM lifecycle tools |
| F2.6 | Container lifecycle tools |
| F2.7 | Storage tools |
| F2.8 | Backup tools |
| F2.9 | Safety system |
| F2.10 | Rollback system |
| F2.11 | Audit logging |
| F2.12 | Testing and documentation |

### Feature 3: Claude Code Integration
| ID | Milestone |
|----|-----------|
| F3.1 | Project setup |
| F3.2 | Core skills |
| F3.3 | Slash commands |
| F3.4 | Hooks configuration |
| F3.5 | Cross-system skills (UniFi integration) |
| F3.6 | Testing and documentation |

### Feature 4: SubAgent Integration
| ID | Milestone |
|----|-----------|
| F4.1 | Project setup |
| F4.2 | Core agent framework |
| F4.3 | Capacity Planner agent |
| F4.4 | Migration Advisor agent |
| F4.5 | Backup Auditor agent |
| F4.6 | Performance Analyzer agent |
| F4.7 | Agent-to-skill integration |
| F4.8 | Testing and documentation |

See individual feature specifications for complete milestone details.

---

## 10. Open Questions

*To be resolved during research phase:*

- [ ] Cluster support needed or single-node sufficient?
- [ ] Integration with Proxmox Backup Server?
- [ ] GPU passthrough requirements?
- [ ] Preferred OS templates to pre-configure?
- [ ] Automation for template updates?
- [ ] Task polling intervals for async operations?

---

## 11. Research Tasks

*Documentation to gather:*

- [ ] Proxmox API documentation review
- [ ] API token vs user authentication trade-offs
- [ ] proxmoxer library capabilities and limitations
- [ ] Cloud-init integration options
- [ ] Template management best practices
- [ ] VLAN-aware bridge configuration
- [ ] Task/job status polling patterns
- [ ] Storage type differences (local, NFS, ZFS, etc.)

---

*Document Version: 2.0*
*Last Updated: 2026-01-11*
*Changelog: v2.0 - Restructured to match Phase 1 format with Features Overview (F1-F4), updated tool organization, added orchestration layer, aligned milestones with feature specs*
