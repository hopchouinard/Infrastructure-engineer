# Homelab Infrastructure Engineer

A Claude Code-powered system for managing homelab infrastructure through natural language.

---

## 1. Vision & Goals

### Mission
Build an AI-powered infrastructure engineer that allows Claude Code to perform network and systems operations in a homelab environment through natural language requests.

### Core Capabilities
Transform high-level requests into executed infrastructure changes. For example:

> "Add my TV to a new isolated VLAN but allow it to access my NAS"

Claude should decompose this into:
1. Create a new VLAN (e.g., VLAN 40 "IoT-Media")
2. Configure switch port tagging for the TV's physical port
3. Create firewall rules allowing TV → NAS on required ports (SMB/NFS)
4. Deny all other inter-VLAN traffic from the new VLAN

### Success Criteria
- [ ] Natural language → infrastructure changes for UniFi ecosystem
- [ ] Tiered safety model prevents accidental damage
- [ ] Audit trail of all changes made
- [ ] Expandable to Proxmox, Home Assistant, and other systems

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
├──────────────┬──────────────┬──────────────┬───────────────────┤
│ Slash Cmds   │    Skills    │    Hooks     │    MCP Client     │
│ /infra-*     │ (orchestr.)  │ (notify)     │                   │
│ (workflows)  │              │              │                   │
└──────────────┴──────────────┴──────────────┴─────────┬─────────┘
                                                        │
┌───────────────────────────────────────────────────────┴─────────┐
│                      MCP Server Layer                            │
├───────────────┬───────────────┬───────────────┬────────────────┤
│  unifi-mcp    │  proxmox-mcp  │    ha-mcp     │   infra-mcp    │
│  (network)    │  (vms/cts)    │  (automation) │  (dns/docker)  │
└───────┬───────┴───────┬───────┴───────┬───────┴────────┬───────┘
        │               │               │                │
        ▼               ▼               ▼                ▼
    [UniFi API]    [Proxmox API]    [HA API]      [Various APIs]
```

### Integration Model (Hybrid)

| Component | Purpose | Example |
|-----------|---------|---------|
| **MCP Servers** | API abstraction layer; expose infrastructure as tools | `unifi-mcp` wraps UniFi Network API |
| **Skills** | Orchestrate multi-step operations | "Isolate device" skill chains VLAN + firewall + port config |
| **Slash Commands** | User-facing workflow triggers | `/infra-audit` runs security audit |
| **Hooks** | Event notifications | Notify when long-running operations complete |

---

## 3. Phase 1: UniFi Infrastructure

### 3.1 Documentation Acquisition

Before building tooling, create a local documentation corpus matched to the exact UniFi versions running.

#### Crawling Strategy
```
Sources:
├── help.ui.com/hc/en-us/categories/   (UniFi Help Center)
├── dl.ubnt.com/guides/UniFi/          (Official PDFs)
└── community.ui.com/                   (Community knowledge)

Schedule: Weekly crawl via script
Output: ai_docs/vendor/unifi/
```

#### Local Exports
From your UniFi console, export:
- Settings backup (JSON)
- Current network topology screenshot
- API endpoint discovery (via browser dev tools or `GET /proxy/network/api/s/default/`)
- UniFi OS and Network Application versions

#### Version Matching
Document the specific versions in use:
```yaml
# ai_docs/vendor/unifi/versions.yaml
unifi_os: "4.x.x"
network_app: "8.x.x"
devices:
  - model: UDM-Pro
    firmware: x.x.x
  - model: USW-24-POE
    firmware: x.x.x
```

### 3.2 unifi-mcp Server Design

#### Authentication
```python
# Stored in environment or secure config
UNIFI_HOST=https://192.168.1.1
UNIFI_USERNAME=api-user
UNIFI_PASSWORD=<secure>
UNIFI_SITE=default
```

Create a dedicated local user in UniFi with appropriate permissions (not your admin account).

#### Tool Categories

**Query Tools (Auto-Approved)**
| Tool | Description |
|------|-------------|
| `list_vlans` | List all VLANs with IDs, names, subnets |
| `list_clients` | List connected clients with IPs, MACs, names |
| `list_devices` | List UniFi devices (switches, APs) |
| `get_client_details` | Get detailed info for a specific client |
| `get_port_status` | Get switch port status and statistics |
| `list_firewall_rules` | List firewall rules by zone/group |
| `get_traffic_stats` | Get traffic statistics for client/network |

**Configuration Tools (Require Confirmation)**
| Tool | Description | Risk Level |
|------|-------------|------------|
| `create_vlan` | Create new VLAN | Medium |
| `delete_vlan` | Delete VLAN | High |
| `set_port_vlan` | Configure switch port VLAN tagging | Medium |
| `create_firewall_rule` | Add firewall rule | High |
| `delete_firewall_rule` | Remove firewall rule | High |
| `modify_firewall_rule` | Edit existing rule | High |
| `rename_client` | Set friendly name for client | Low |
| `block_client` | Block client from network | Medium |

**Diagnostic Tools (Auto-Approved)**
| Tool | Description |
|------|-------------|
| `ping_client` | Ping client from UDM |
| `get_topology` | Get network topology |
| `check_port_connectivity` | Test if port is connected |

#### Error Handling
- All API errors surfaced with clear messages
- Validation before attempting changes (e.g., check VLAN ID not in use)
- Timeout handling for long operations

#### Rollback Considerations
- Before any configuration change, capture current state
- Store rollback data in memory for the session
- Provide `undo_last_change` tool for immediate rollback

### 3.3 Atomic Skills Catalog (UniFi)

Each atomic skill maps to one or more MCP tools.

#### VLAN Operations
| Skill | Tools Used | Confirmation |
|-------|-----------|--------------|
| Create VLAN | `create_vlan` | Yes |
| Delete VLAN | `list_clients`, `delete_vlan` | Yes (warns if clients exist) |
| List VLANs | `list_vlans` | No |
| Get VLAN details | `list_vlans`, `list_clients` | No |

#### Firewall Management
| Skill | Tools Used | Confirmation |
|-------|-----------|--------------|
| Create allow rule | `create_firewall_rule` | Yes |
| Create deny rule | `create_firewall_rule` | Yes |
| List rules | `list_firewall_rules` | No |
| Delete rule | `delete_firewall_rule` | Yes |
| Enable/disable rule | `modify_firewall_rule` | Yes |

#### Switch Port Configuration
| Skill | Tools Used | Confirmation |
|-------|-----------|--------------|
| Set port VLAN | `set_port_vlan` | Yes |
| Get port status | `get_port_status` | No |
| Identify port (blink) | `identify_port` | No |

#### Client Management
| Skill | Tools Used | Confirmation |
|-------|-----------|--------------|
| Find client | `list_clients`, `get_client_details` | No |
| Rename client | `rename_client` | Yes (low risk) |
| Block client | `block_client` | Yes |
| Unblock client | `unblock_client` | Yes |

### 3.4 Orchestration Skills

Complex operations that chain multiple atomic skills.

#### Example: Isolate Device to New VLAN with Selective Access

**Trigger:** "Add my TV to a new isolated VLAN but allow it to access my NAS"

**Skill Decomposition:**
```
1. [Query] Find TV client by name/MAC
2. [Query] Find NAS client to get its IP/VLAN
3. [Query] Find available VLAN ID
4. [Query] Find switch port where TV is connected
5. [Config] Create new VLAN (e.g., "IoT-Media", VLAN 40)
6. [Config] Set switch port to new VLAN
7. [Config] Create firewall rule: VLAN 40 → NAS IP on ports 445,139 (SMB)
8. [Config] Create firewall rule: Deny VLAN 40 → all other VLANs
```

**Confirmation Flow:**
```
Claude: I've analyzed the request. Here's my plan:

1. Create VLAN 40 "IoT-Media" (subnet 192.168.40.0/24)
2. Move TV (MAC: aa:bb:cc:dd:ee:ff) from port 12 on USW-24-POE to VLAN 40
3. Create firewall rules:
   - ALLOW: 192.168.40.0/24 → 192.168.1.50 (NAS) on TCP 445,139
   - DENY: 192.168.40.0/24 → RFC1918 (block other internal traffic)

Shall I proceed? [Yes/No/Modify]
```

#### Other Orchestration Examples
- **Guest network setup**: Create VLAN + SSID + firewall isolation + bandwidth limits
- **IoT quarantine**: Move suspicious device to isolated VLAN + alert
- **Port security audit**: Scan all ports, identify unknown MACs, report
- **Network documentation**: Generate current topology, VLANs, rules as markdown

---

## 4. Future Phases (High-Level)

### Phase 2: Proxmox Integration
- `proxmox-mcp` server wrapping Proxmox API
- VM/Container lifecycle management
- Storage management
- Backup operations
- Network bridge configuration (ties into UniFi VLANs)

### Phase 3: Home Automation
- `ha-mcp` server wrapping Home Assistant API
- Device control and automation
- Scene management
- Integration with network (e.g., presence detection via UniFi clients)

### Phase 4: Supporting Services
- `infra-mcp` for miscellaneous services:
  - DNS management (Pi-hole, AdGuard, etc.)
  - Docker container management
  - Monitoring integration (Grafana, Prometheus)
  - Certificate management

### Cross-System Orchestration
Once multiple MCP servers exist, enable cross-system workflows:
- "Spin up a new VM, assign it to the IoT VLAN, and add it to Home Assistant"
- "When guest WiFi client connects, create temporary Proxmox container for isolated browsing"

---

## 5. Safety & Permissions Framework

### Tiered Permission Model

| Tier | Operations | Behavior |
|------|-----------|----------|
| **Read** | Query, list, get status | Auto-approved, no confirmation |
| **Low Risk** | Rename, cosmetic changes | Brief confirmation |
| **Medium Risk** | VLAN creation, port changes | Detailed confirmation with preview |
| **High Risk** | Firewall rules, deletions | Explicit confirmation + show rollback option |
| **Critical** | Factory reset, firmware update | Require explicit user initiation, not AI-suggested |

### Confirmation UI Pattern
For Medium/High risk operations:
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️  Configuration Change Required                           │
├─────────────────────────────────────────────────────────────┤
│ Operation: Create VLAN                                      │
│ Details:                                                    │
│   - Name: IoT-Media                                         │
│   - VLAN ID: 40                                             │
│   - Subnet: 192.168.40.0/24                                 │
│   - Gateway: 192.168.40.1                                   │
│                                                             │
│ Risk Level: Medium                                          │
│ Reversible: Yes (delete VLAN)                               │
├─────────────────────────────────────────────────────────────┤
│ [Proceed] [Cancel] [Modify]                                 │
└─────────────────────────────────────────────────────────────┘
```

### Audit Logging
All operations logged to `ai_docs/logs/infra-changes.log`:
```json
{
  "timestamp": "2025-01-09T19:30:00Z",
  "operation": "create_vlan",
  "parameters": {"name": "IoT-Media", "vlan_id": 40},
  "result": "success",
  "user_confirmed": true,
  "rollback_data": {"vlan_id": 40}
}
```

### Guardrails
- Never modify management VLAN
- Never delete VLAN with active clients without explicit acknowledgment
- Never create "allow all" firewall rules
- Rate limit: Max 5 configuration changes per minute
- Dry-run mode available for testing

---

## 6. Development Roadmap

### Phase 1 Milestones (UniFi)

| Milestone | Deliverable |
|-----------|-------------|
| M1.1 | Documentation corpus created (crawled + local exports) |
| M1.2 | `unifi-mcp` server with query tools only |
| M1.3 | Add configuration tools with confirmation flow |
| M1.4 | First orchestration skill working end-to-end |
| M1.5 | Audit logging and rollback capability |
| M1.6 | Slash commands for common workflows |

### Testing Strategy
- **Unit tests**: Each MCP tool tested against mock API responses
- **Integration tests**: Test against real UniFi in a maintenance window
- **Dry-run mode**: All config tools support `dry_run=true` to preview without applying
- **Staging network**: Consider a small isolated network for testing (single AP + switch)

### Expansion Checkpoints
Before starting Phase 2 (Proxmox):
- [ ] Phase 1 milestones complete
- [ ] No critical bugs in unifi-mcp
- [ ] User has successfully completed 5+ real operations
- [ ] Rollback tested and working

---

## Appendix A: File Structure

```
Infrastructure-engineer/
├── ai_docs/
│   ├── spec/
│   │   └── masteridea.md          # This document
│   ├── vendor/
│   │   └── unifi/
│   │       ├── versions.yaml      # Version tracking
│   │       ├── api/               # Crawled API docs
│   │       └── guides/            # Crawled PDFs/guides
│   └── logs/
│       └── infra-changes.log      # Audit log
├── mcp-servers/
│   ├── unifi-mcp/
│   │   ├── src/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── [future servers]/
├── skills/
│   └── [skill definitions]/
└── .claude/
    └── settings.json              # MCP server configuration
```

## Appendix B: UniFi API Reference

Key endpoints (UniFi Network Application):
```
Base: https://{host}/proxy/network/api/s/{site}/

GET  /stat/sta           # List clients
GET  /stat/device        # List devices
GET  /rest/networkconf   # List networks/VLANs
POST /rest/networkconf   # Create network/VLAN
GET  /rest/firewallrule  # List firewall rules
POST /rest/firewallrule  # Create firewall rule
POST /cmd/stamgr         # Client management commands
```

Authentication: Session cookie from `POST /api/auth/login`

---

*Document Version: 1.0*
*Last Updated: 2025-01-09*
