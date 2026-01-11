# Phase 1: UniFi Infrastructure

Detailed specification for building the UniFi MCP server and associated tooling.

**Parent Document:** [masteridea.md](./masteridea.md)
**Status:** Planning
**Target Hardware:** UDM + UniFi Switches + UniFi Access Points

---

## Features Overview

Phase 1 consists of four features:

| Feature | Name | Spec Document | Description |
|---------|------|---------------|-------------|
| F1 | Documentation Crawler | [phase1-f1-documentation-crawler.md](./phase1-f1-documentation-crawler.md) | Crawls UniFi docs for offline use |
| F2 | UniFi MCP Server | [phase1-f2-unifi-mcp-server.md](./phase1-f2-unifi-mcp-server.md) | Exposes UniFi API as MCP tools |
| F3 | Claude Code Integration | [phase1-f3-claude-code-integration.md](./phase1-f3-claude-code-integration.md) | Skills, slash commands, hooks |
| F4 | SubAgent Integration | [phase1-f4-subagent-integration.md](./phase1-f4-subagent-integration.md) | Specialized autonomous agents for complex analysis |

**See individual feature specifications for detailed requirements.**

---

## 1. Prerequisites

### 1.1 Hardware Inventory

Before implementation, document your UniFi ecosystem:

```yaml
# To be filled in during research phase
controller:
  model: ""           # e.g., UDM-Pro, UDM-SE, UDM
  ip: ""              # e.g., 192.168.1.1
  unifi_os_version: ""
  network_app_version: ""

switches:
  - model: ""
    name: ""
    ip: ""
    firmware: ""
    port_count: 0
    poe: false

access_points:
  - model: ""
    name: ""
    ip: ""
    firmware: ""
```

### 1.2 API Access Setup

**Step 1: Create dedicated API user**
1. UniFi OS Settings → Admins → Add Admin
2. Role: Limited Admin (or custom role with API access)
3. Username: `claude-api` (or similar)
4. Enable: Local Access Only (no cloud)
5. Document credentials securely (not in this repo)

**Step 2: Verify API access**
```bash
# Test authentication
curl -k -X POST https://{UDM_IP}/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"claude-api","password":"YOUR_PASSWORD"}'

# Should return session cookie
```

**Step 3: Discover API endpoints**
- Use browser dev tools on UniFi web UI
- Document available endpoints for your version
- Note any version-specific differences

### 1.3 Network Baseline

Document current network state before making any changes:

| Item | Current Value | Notes |
|------|---------------|-------|
| Management VLAN | | Never modify |
| VLAN range in use | | e.g., 1-10 |
| Reserved VLAN range | | For future automation |
| IP scheme | | e.g., 192.168.x.0/24 |
| Firewall rule count | | Baseline |

---

## 2. Documentation Corpus

### 2.1 Crawl Sources

| Source | URL Pattern | Content Type | Priority |
|--------|-------------|--------------|----------|
| Help Center | `help.ui.com/hc/en-us/articles/*` | HTML | High |
| Guides | `dl.ubnt.com/guides/UniFi/*` | PDF | High |
| Community | `community.ui.com/questions/*` | HTML | Medium |
| API (unofficial) | Various GitHub repos | Markdown | High |

### 2.2 Crawl Script Requirements

```python
# Pseudocode for documentation crawler
class UniFiDocCrawler:
    """
    Crawl UniFi documentation for offline use.

    Features needed:
    - Respect robots.txt
    - Rate limiting (1 req/sec)
    - HTML → Markdown conversion
    - PDF download and text extraction
    - Version tagging in output
    - Incremental updates (only new/changed)
    """

    def crawl_help_center(self):
        # Categories to crawl:
        # - UniFi Network Application
        # - UniFi OS
        # - UniFi Gateway (firewall)
        pass

    def crawl_guides(self):
        # PDF guides from dl.ubnt.com
        pass

    def extract_api_docs(self):
        # Parse API documentation from various sources
        pass
```

### 2.3 Local Exports

From your UniFi console, export:

| Export | Location in UI | Format | Purpose |
|--------|----------------|--------|---------|
| Settings backup | Settings → Backup | .unf | Full config reference |
| Site export | Settings → Site | JSON | Site-specific config |
| Client list | Clients → Export | CSV | Current client inventory |
| Network diagram | (screenshot) | PNG | Visual reference |

### 2.4 Output Structure

```
ai_docs/vendor/unifi/
├── versions.yaml           # Version tracking
├── api/
│   ├── endpoints.md        # Discovered endpoints
│   ├── authentication.md   # Auth flow documentation
│   ├── clients.md          # Client management API
│   ├── networks.md         # VLAN/network API
│   ├── firewall.md         # Firewall rules API
│   ├── devices.md          # Device management API
│   └── examples/           # Request/response examples
├── guides/
│   ├── [downloaded PDFs]
│   └── [converted markdown]
├── help-center/
│   └── [crawled articles as markdown]
└── local-exports/
    ├── backup-YYYY-MM-DD.unf
    ├── site-config.json
    └── topology.png
```

---

## 3. MCP Server: `unifi-mcp`

### 3.1 Project Structure

See [phase1-f2-unifi-mcp-server.md](./phase1-f2-unifi-mcp-server.md) Section 4 for the detailed project structure.

**Key points:**
- Uses **FastMCP pattern** with `@mcp.tool()` decorators for tool registration
- Tools defined inline in `server.py`, logic in `tools/query/` and `tools/config/` subdirectories
- Separate `safety/` module for validation, rate limiting, and rollback
- Comprehensive test fixtures in `tests/fixtures/api_responses/`

```
mcp-servers/unifi-mcp/
├── src/unifi_mcp/
│   ├── server.py               # MCP server with FastMCP
│   ├── config.py               # Configuration management
│   ├── client/                 # UniFi API client
│   ├── tools/                  # Tool implementations
│   │   ├── query/              # Query tool functions
│   │   └── config/             # Config tool functions
│   ├── models/                 # Data models
│   ├── safety/                 # Validation, tiers, rollback
│   └── logging/                # Audit logging
├── tests/
├── pyproject.toml
└── README.md
```

### 3.2 Dependencies

```toml
[project]
name = "unifi-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",              # MCP SDK
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

class UniFiConfig(BaseSettings):
    """Configuration loaded from environment."""

    unifi_host: str                    # https://192.168.1.1
    unifi_username: str                # claude-api
    unifi_password: str                # (from secure store)
    unifi_site: str = "default"        # Site name
    unifi_verify_ssl: bool = False     # Self-signed certs

    # Safety settings
    dry_run: bool = False              # Preview mode
    require_confirmation: bool = True  # For config changes
    max_changes_per_minute: int = 5    # Rate limit

    # Logging
    audit_log_path: str = "ai_docs/logs/infra-changes.log"

    class Config:
        env_file = ".env"
```

### 3.4 API Client

```python
# src/client.py - Pseudocode
class UniFiClient:
    """Wrapper for UniFi Network API."""

    def __init__(self, config: UniFiConfig):
        self.config = config
        self.session = None
        self._csrf_token = None

    async def login(self) -> bool:
        """Authenticate and obtain session cookie."""
        pass

    async def logout(self) -> None:
        """End session."""
        pass

    async def request(
        self,
        method: str,
        endpoint: str,
        data: dict = None
    ) -> dict:
        """Make authenticated API request."""
        pass

    # Query methods
    async def list_clients(self) -> list[Client]:
        """GET /stat/sta"""
        pass

    async def list_networks(self) -> list[Network]:
        """GET /rest/networkconf"""
        pass

    async def list_devices(self) -> list[Device]:
        """GET /stat/device"""
        pass

    async def list_firewall_rules(self, ruleset: str) -> list[FirewallRule]:
        """GET /rest/firewallrule"""
        pass

    # Config methods
    async def create_network(self, network: NetworkCreate) -> Network:
        """POST /rest/networkconf"""
        pass

    async def delete_network(self, network_id: str) -> bool:
        """DELETE /rest/networkconf/{id}"""
        pass

    async def create_firewall_rule(self, rule: FirewallRuleCreate) -> FirewallRule:
        """POST /rest/firewallrule"""
        pass
```

---

## 4. Tool Specifications

### 4.1 Query Tools (Auto-Approved)

#### `unifi_list_networks`
```yaml
name: unifi_list_networks
description: List all networks/VLANs configured on the UniFi controller
parameters:
  - name: include_default
    type: boolean
    default: true
    description: Include the default network
  - name: vlan_only
    type: boolean
    default: false
    description: Only return networks with VLAN IDs
returns:
  type: array
  items:
    - id: string          # UniFi internal ID
    - name: string        # Human-readable name
    - vlan_id: integer    # 802.1Q VLAN ID
    - subnet: string      # e.g., "192.168.10.0/24"
    - dhcp_enabled: boolean
    - purpose: string     # "corporate", "guest", "iot", etc.
permission_level: read
```

#### `unifi_list_clients`
```yaml
name: unifi_list_clients
description: List all clients currently connected or recently seen
parameters:
  - name: filter_network
    type: string
    required: false
    description: Filter by network/VLAN name
  - name: filter_type
    type: string
    enum: [wired, wireless, all]
    default: all
  - name: include_offline
    type: boolean
    default: false
returns:
  type: array
  items:
    - mac: string
    - ip: string
    - hostname: string
    - name: string        # User-assigned name
    - network: string
    - is_wired: boolean
    - switch_port: string # e.g., "USW-24-POE:12"
    - ap_name: string     # For wireless
    - last_seen: datetime
permission_level: read
```

#### `unifi_list_devices`
```yaml
name: unifi_list_devices
description: List all UniFi devices (switches, APs, gateways)
parameters: {}
returns:
  type: array
  items:
    - mac: string
    - name: string
    - model: string       # e.g., "USW-24-POE"
    - type: string        # "usw", "uap", "ugw"
    - ip: string
    - firmware: string
    - uptime: integer
    - status: string      # "online", "offline", "adopting"
permission_level: read
```

#### `unifi_get_client`
```yaml
name: unifi_get_client
description: Get detailed information about a specific client
parameters:
  - name: identifier
    type: string
    required: true
    description: MAC address, IP, or client name
returns:
  - mac: string
  - ip: string
  - hostname: string
  - name: string
  - oui: string           # Manufacturer from MAC
  - network: string
  - vlan_id: integer
  - is_wired: boolean
  - switch_mac: string
  - switch_port: integer
  - ap_mac: string
  - channel: integer
  - signal: integer       # dBm
  - tx_bytes: integer
  - rx_bytes: integer
  - uptime: integer
  - first_seen: datetime
  - last_seen: datetime
  - blocked: boolean
permission_level: read
```

#### `unifi_get_port_status`
```yaml
name: unifi_get_port_status
description: Get status of a specific switch port
parameters:
  - name: switch
    type: string
    required: true
    description: Switch name or MAC
  - name: port
    type: integer
    required: true
    description: Port number
returns:
  - port_id: integer
  - name: string
  - enabled: boolean
  - speed: integer        # Mbps
  - duplex: string        # "full", "half"
  - poe_mode: string      # "auto", "off", "24v", "48v"
  - poe_power: float      # Watts
  - native_vlan: integer
  - tagged_vlans: array[integer]
  - stp_state: string
  - connected_client: string  # MAC if connected
permission_level: read
```

#### `unifi_list_firewall_rules`
```yaml
name: unifi_list_firewall_rules
description: List firewall rules for a specific ruleset
parameters:
  - name: ruleset
    type: string
    enum: [LAN_IN, LAN_OUT, LAN_LOCAL, GUEST_IN, GUEST_OUT, WAN_IN, WAN_OUT, WAN_LOCAL]
    required: true
returns:
  type: array
  items:
    - id: string
    - name: string
    - enabled: boolean
    - action: string      # "accept", "drop", "reject"
    - protocol: string    # "tcp", "udp", "all", etc.
    - source: object
        - type: string    # "network", "ip", "group"
        - value: string
    - destination: object
        - type: string
        - value: string
    - port: string        # "any", "80", "80,443", "1000-2000"
    - rule_index: integer # Order in ruleset
permission_level: read
```

### 4.2 Configuration Tools (Require Confirmation)

#### `unifi_create_network`
```yaml
name: unifi_create_network
description: Create a new network/VLAN
parameters:
  - name: name
    type: string
    required: true
    description: Human-readable network name
  - name: vlan_id
    type: integer
    required: true
    description: 802.1Q VLAN ID (1-4094)
  - name: subnet
    type: string
    required: true
    description: CIDR notation (e.g., "192.168.40.0/24")
  - name: gateway
    type: string
    required: false
    description: Gateway IP (defaults to .1)
  - name: dhcp_enabled
    type: boolean
    default: true
  - name: dhcp_start
    type: string
    required: false
  - name: dhcp_stop
    type: string
    required: false
  - name: purpose
    type: string
    enum: [corporate, guest, iot, remote-user-vpn, vlan-only]
    default: corporate
validation:
  - vlan_id must not be in use
  - vlan_id must not be 1 (default) or management VLAN
  - subnet must not overlap existing networks
permission_level: medium
rollback: delete created network
```

#### `unifi_delete_network`
```yaml
name: unifi_delete_network
description: Delete a network/VLAN
parameters:
  - name: identifier
    type: string
    required: true
    description: Network name, ID, or VLAN ID
validation:
  - Warn if clients currently on this network
  - Cannot delete management network
  - Cannot delete default network
permission_level: high
rollback: recreate network with same config
```

#### `unifi_set_port_vlan`
```yaml
name: unifi_set_port_vlan
description: Configure VLAN settings for a switch port
parameters:
  - name: switch
    type: string
    required: true
  - name: port
    type: integer
    required: true
  - name: native_vlan
    type: integer
    required: false
    description: Untagged VLAN
  - name: tagged_vlans
    type: array[integer]
    required: false
    description: Tagged VLANs (trunk)
  - name: port_profile
    type: string
    required: false
    description: Use predefined port profile
validation:
  - VLANs must exist
  - Cannot change uplink ports
permission_level: medium
rollback: restore previous port config
```

#### `unifi_create_firewall_rule`
```yaml
name: unifi_create_firewall_rule
description: Create a new firewall rule
parameters:
  - name: name
    type: string
    required: true
  - name: ruleset
    type: string
    enum: [LAN_IN, LAN_OUT, LAN_LOCAL, GUEST_IN, GUEST_OUT, WAN_IN, WAN_OUT, WAN_LOCAL]
    required: true
  - name: action
    type: string
    enum: [accept, drop, reject]
    required: true
  - name: protocol
    type: string
    enum: [all, tcp, udp, tcp_udp, icmp]
    default: all
  - name: source_type
    type: string
    enum: [any, network, ip, ip_range, group]
    required: true
  - name: source_value
    type: string
    required: false
    description: Required unless source_type is "any"
  - name: destination_type
    type: string
    enum: [any, network, ip, ip_range, group]
    required: true
  - name: destination_value
    type: string
    required: false
  - name: port
    type: string
    default: any
    description: Single port, comma-separated, or range
  - name: position
    type: string
    enum: [first, last, before:<rule_id>, after:<rule_id>]
    default: last
validation:
  - No "allow any any" rules
  - Source and destination must be valid
  - Rule order matters - verify position
permission_level: high
rollback: delete created rule
```

#### `unifi_delete_firewall_rule`
```yaml
name: unifi_delete_firewall_rule
description: Delete a firewall rule
parameters:
  - name: rule_id
    type: string
    required: true
permission_level: high
rollback: recreate rule with same config
```

#### `unifi_rename_client`
```yaml
name: unifi_rename_client
description: Set a friendly name for a client
parameters:
  - name: mac
    type: string
    required: true
  - name: name
    type: string
    required: true
permission_level: low
rollback: restore previous name
```

#### `unifi_block_client`
```yaml
name: unifi_block_client
description: Block a client from connecting
parameters:
  - name: mac
    type: string
    required: true
permission_level: medium
rollback: unblock client
```

### 4.3 Complete Tool Summary

See [phase1-f2-unifi-mcp-server.md](./phase1-f2-unifi-mcp-server.md) Section 7.6 for the complete tool list.

| Category | Tools |
|----------|-------|
| **Query (READ)** | `unifi_list_networks`, `unifi_get_network`, `unifi_list_clients`, `unifi_get_client`, `unifi_search_clients`, `unifi_list_devices`, `unifi_get_device`, `unifi_list_firewall_rules`, `unifi_get_firewall_rule`, `unifi_get_port_status`, `unifi_get_client_on_port` |
| **Config (MEDIUM)** | `unifi_create_network`, `unifi_update_network`, `unifi_set_port_vlan`, `unifi_block_client`, `unifi_unblock_client` |
| **Config (HIGH)** | `unifi_delete_network`, `unifi_create_firewall_rule`, `unifi_delete_firewall_rule`, `unifi_undo` |
| **Config (LOW)** | `unifi_rename_client` |

---

## 5. Orchestration Layer

This section provides a high-level overview. See feature specifications for detailed implementations:
- **Feature 3:** [phase1-f3-claude-code-integration.md](./phase1-f3-claude-code-integration.md) - Skills, Commands, Hooks
- **Feature 4:** [phase1-f4-subagent-integration.md](./phase1-f4-subagent-integration.md) - SubAgents for complex analysis

### 5.1 Native Skill System

Skills use **Claude Code's native skill system** - markdown instruction files in `.claude/skills/` that Claude follows when activated.

**Core Skills:**
| Skill | Purpose |
|-------|---------|
| `unifi-infra` | Core infrastructure management (isolation, finding, blocking) |
| `guest-network` | Guest WiFi creation with isolation |
| `security-audit` | Network security analysis |

### 5.2 Slash Commands

Commands in `.claude/commands/` provide explicit, user-invoked workflows:

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

### 5.3 SubAgents (Feature 4)

Specialized autonomous agents for complex analysis tasks:

| Agent | Purpose |
|-------|---------|
| **Design Advisor** | Network architecture consultation |
| **Troubleshooter** | Complex connectivity diagnostics |
| **Security Deep Audit** | Comprehensive security analysis |
| **Change Planner** | Multi-resource change planning |

SubAgents operate read-only and produce **Execution Plans** for user review.

### 5.4 Hooks

Event-driven shell scripts in `.claude/hooks/` for validation and logging:

| Hook | Purpose |
|------|---------|
| `pre-delete-network.sh` | Blocks deletion of protected networks |
| `pre-firewall-rule.sh` | Blocks dangerous firewall rules |
| `post-change-log.sh` | Logs configuration changes |

---

## 6. Confirmation Flow

### 6.1 Change Plan Object

```python
@dataclass
class ChangePlan:
    """Represents a set of changes to be confirmed."""

    id: str                          # Unique plan ID
    description: str                 # Human summary
    changes: list[Change]            # Ordered list of changes
    risk_level: RiskLevel            # Aggregated risk
    estimated_impact: str            # What will be affected
    rollback_available: bool         # Can we undo?

    def to_confirmation_prompt(self) -> str:
        """Generate markdown for user confirmation."""
        pass

    async def execute(self) -> ExecutionResult:
        """Execute all changes in order."""
        pass

    async def rollback(self) -> RollbackResult:
        """Undo all changes in reverse order."""
        pass
```

### 6.2 Confirmation Prompt Template

```markdown
## Proposed Changes

**Operation:** {description}
**Risk Level:** {risk_level}

### Changes to Apply:

{for change in changes}
{change.index}. **{change.type}**: {change.summary}
   - {change.details}
{/for}

### Impact:
{estimated_impact}

### Rollback:
{if rollback_available}
These changes can be undone with `/infra-undo`
{else}
**Warning:** Some changes cannot be automatically undone
{/if}

---
**Proceed with these changes?** [Yes] [No] [Modify]
```

---

## 7. Rollback System

### 7.1 Rollback Data Structure

```python
@dataclass
class RollbackEntry:
    """Stored data for undoing a change."""

    timestamp: datetime
    change_type: str              # "create_vlan", "set_port", etc.
    forward_params: dict          # What was applied
    reverse_params: dict          # What to apply to undo
    original_state: dict          # State before change
    expiry: datetime              # Auto-expire after 24h
```

### 7.2 Rollback Storage

```python
class RollbackManager:
    """Manages rollback data for the session."""

    def __init__(self, max_entries: int = 100):
        self._entries: list[RollbackEntry] = []

    def record(self, entry: RollbackEntry) -> str:
        """Record a change for potential rollback. Returns rollback ID."""
        pass

    async def undo_last(self) -> RollbackResult:
        """Undo the most recent change."""
        pass

    async def undo(self, rollback_id: str) -> RollbackResult:
        """Undo a specific change."""
        pass

    def list_available(self) -> list[RollbackEntry]:
        """List changes that can be undone."""
        pass
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

Mock UniFi API responses for all tool tests:

```python
# tests/test_tools_query.py
import pytest
from respx import MockRouter

@pytest.fixture
def mock_unifi(respx_mock: MockRouter):
    respx_mock.get("/api/s/default/stat/sta").respond(json={
        "data": [
            {"mac": "aa:bb:cc:dd:ee:ff", "ip": "192.168.1.100", ...}
        ]
    })
    return respx_mock

async def test_list_clients(mock_unifi, unifi_client):
    clients = await unifi_client.list_clients()
    assert len(clients) == 1
    assert clients[0].mac == "aa:bb:cc:dd:ee:ff"
```

### 8.2 Integration Tests

Run against real UniFi in controlled conditions:

```python
# tests/integration/test_real_unifi.py
import pytest

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("UNIFI_INTEGRATION"), reason="Integration tests disabled")
async def test_list_vlans_real():
    client = UniFiClient.from_env()
    await client.login()
    vlans = await client.list_vlans()
    assert len(vlans) > 0
    await client.logout()
```

### 8.3 Dry Run Mode

All config tools support `dry_run=True`:

```python
async def create_vlan(self, params: CreateVLANParams) -> VLANResult:
    if self.config.dry_run:
        return VLANResult(
            success=True,
            dry_run=True,
            would_create=params.to_dict(),
            message="Dry run: VLAN would be created"
        )
    # Actually create VLAN
```

---

## 9. Milestones

Phase 1 milestones are tracked at the feature level. See individual specifications for detailed task breakdowns.

### Feature 1: Documentation Crawler
| ID | Milestone |
|----|-----------|
| F1.1 | Project setup |
| F1.2 | Fetcher implementation |
| F1.3 | Help Center adapter |
| F1.4 | Guides adapter (DEFERRED) |
| F1.5-F1.10 | Converters, state management, CLI, testing, docs |

### Feature 2: UniFi MCP Server
| ID | Milestone |
|----|-----------|
| F2.1 | Project setup |
| F2.2 | Configuration |
| F2.3 | API client |
| F2.4 | Query tools |
| F2.5 | Config tools |
| F2.6-F2.11 | Safety system, rollback, audit logging, MCP integration, testing, docs |

### Feature 3: Claude Code Integration
| ID | Milestone |
|----|-----------|
| F3.1 | Project setup |
| F3.2 | Core skills |
| F3.3 | Slash commands |
| F3.4 | Hooks configuration |
| F3.5-F3.7 | Additional skills, testing, documentation |

### Feature 4: SubAgent Integration
| ID | Milestone |
|----|-----------|
| F4.1 | Project setup |
| F4.2 | Core agent framework |
| F4.3-F4.6 | Individual agents (Design, Troubleshoot, Security, Change) |
| F4.7-F4.9 | Agent-to-skill integration, testing, documentation |

See individual feature specifications for complete milestone details.

---

## 10. Open Questions

*To be resolved during research phase:*

- [ ] Exact API endpoints for current UniFi versions?
- [ ] Rate limits on UniFi API?
- [ ] Best approach for real-time status updates?
- [ ] How to handle multi-site setups?
- [ ] Webhook support for change notifications?

---

## 11. Research Tasks

*Documentation to gather:*

- [ ] UniFi Network API documentation (official + community)
- [ ] UniFi OS authentication flow details
- [ ] Firewall rule ordering and precedence
- [ ] Port profile schema and options
- [ ] DHCP configuration options
- [ ] Rate limiting and session management

---

*Document Version: 1.1*
*Last Updated: 2026-01-10*
*Changelog: v1.1 - Added Features Overview (F1-F4), updated tool names (vlans→networks), updated orchestration section to reflect native skill system, aligned milestones with feature specs, updated project structure to reference FastMCP pattern*
