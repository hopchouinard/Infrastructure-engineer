# Phase 1 - Feature 2: UniFi MCP Server

The core MCP server that exposes UniFi Network operations as tools for Claude Code.

**Parent Document:** [phase1-unifi.md](./phase1-unifi.md)
**Dependencies:**
- Feature 1 (Documentation Crawler) - for implementation guidance
- UniFi API access credentials
**Status:** Planning

---

## 1. Purpose

### 1.1 What This Feature Does

The `unifi-mcp` server is a Model Context Protocol server that:
- Connects to your UniFi Network controller
- Exposes network operations as MCP tools
- Handles authentication and session management
- Enforces safety tiers (read vs. write operations)
- Provides rollback capabilities for configuration changes

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| UniFi Network API operations | UniFi Protect (cameras) |
| VLAN/Network management | UniFi Access (door locks) |
| Firewall rules | UniFi Talk (VoIP) |
| Client management | UniFi Connect (displays) |
| Switch port configuration | Multi-site management (initially) |
| Device status queries | Firmware updates |
| Traffic statistics | Factory reset operations |

### 1.3 Design Principles

1. **Safety First:** Destructive operations require confirmation
2. **Transparency:** All operations are logged
3. **Reversibility:** Configuration changes can be rolled back
4. **Least Privilege:** Use minimal API permissions needed
5. **Fail Safe:** Validation before execution

---

## 2. Prerequisites

### 2.1 UniFi API Access

**Required before implementation:**

```yaml
# Credentials (store securely, not in repo)
unifi:
  host: "https://192.168.1.1"  # Your UDM IP
  username: "claude-api"        # Dedicated API user
  password: "<secure>"          # From password manager
  site: "default"               # Site name
```

**API User Setup:**
1. Create local user in UniFi OS: Settings → Admins → Add
2. Role: "Limited Admin" or custom role with:
   - Network: Full access
   - System: Read-only (for device info)
3. Verify login works via API

### 2.2 Network Access

- Claude Code must be able to reach UniFi controller
- Self-signed certificate handling (skip verification or add to trust store)
- Consider VPN if running Claude Code outside home network

---

## 3. Architecture

### 3.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code                               │
│                         │                                    │
│                    MCP Protocol                              │
│                         │                                    │
└─────────────────────────┼───────────────────────────────────┘
                          │
┌─────────────────────────┼───────────────────────────────────┐
│                   unifi-mcp server                           │
├─────────────────────────┼───────────────────────────────────┤
│                         ▼                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    Tool Router                       │    │
│  │   Routes tool calls to appropriate handlers          │    │
│  └───────────────────────┬─────────────────────────────┘    │
│                          │                                   │
│  ┌───────────┬───────────┼───────────┬───────────┐          │
│  │           │           │           │           │          │
│  ▼           ▼           ▼           ▼           ▼          │
│ ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐            │
│ │Query│   │Config│  │Diag │   │Audit│   │Roll │            │
│ │Tools│   │Tools │  │Tools│   │ Log │   │back │            │
│ └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘   └──┬──┘            │
│    │         │         │         │         │                │
│    └─────────┴─────────┴─────────┴─────────┘                │
│                          │                                   │
│  ┌───────────────────────┴─────────────────────────────┐    │
│  │                 UniFi API Client                     │    │
│  │   Session management, request/response handling      │    │
│  └───────────────────────┬─────────────────────────────┘    │
│                          │                                   │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │  UniFi API   │
                    │  (UDM/UDR)   │
                    └──────────────┘
```

### 3.2 Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Tool Router** | Parse MCP tool calls, dispatch to handlers |
| **Query Tools** | Read-only operations (list, get, status) |
| **Config Tools** | Write operations (create, update, delete) |
| **Diagnostic Tools** | Network diagnostics (ping, trace) |
| **Audit Log** | Record all operations for review |
| **Rollback Manager** | Store state for undo operations |
| **UniFi API Client** | HTTP client, auth, session management |

---

## 4. Project Structure

### 4.1 Directory Layout

**Note:** This project uses the FastMCP pattern for tool registration. Tools are defined inline using `@mcp.tool()` decorators in `server.py` (see F2.9), not as separate class files.

```
mcp-servers/unifi-mcp/
├── src/
│   └── unifi_mcp/
│       ├── __init__.py
│       ├── server.py               # MCP server with FastMCP (F2.9)
│       ├── config.py               # Configuration (F2.2)
│       ├── config_loader.py        # Config file loading (F2.2)
│       ├── secrets.py              # Secret management (F2.2)
│       ├── errors.py               # Custom exceptions
│       ├── client/
│       │   ├── __init__.py
│       │   ├── api.py              # UniFi API client (F2.3)
│       │   ├── auth.py             # Authentication handler (F2.3)
│       │   ├── session.py          # Session management (F2.3)
│       │   └── types.py            # API response types (F2.3)
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── helpers.py          # Response formatting helpers
│       │   ├── query/              # Query tool functions (F2.4)
│       │   │   ├── __init__.py
│       │   │   ├── networks.py
│       │   │   ├── clients.py
│       │   │   ├── devices.py
│       │   │   ├── firewall.py
│       │   │   └── ports.py
│       │   └── config/             # Config tool functions (F2.5)
│       │       ├── __init__.py
│       │       ├── networks.py
│       │       ├── clients.py
│       │       ├── firewall.py
│       │       └── ports.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── client.py           # Client data models
│       │   ├── network.py          # Network/VLAN models
│       │   ├── firewall.py         # Firewall rule models
│       │   ├── device.py           # Device models
│       │   └── port.py             # Port models
│       ├── safety/
│       │   ├── __init__.py
│       │   ├── tiers.py            # Permission tier definitions
│       │   ├── validation.py       # Pre-execution validation (F2.6)
│       │   ├── rate_limiter.py     # Rate limiting (F2.6)
│       │   └── rollback.py         # Rollback management (F2.7)
│       └── logging/
│           ├── __init__.py
│           └── audit.py            # Audit logging (F2.8)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_config.py              # Configuration tests (F2.2)
│   ├── test_client/
│   │   └── __init__.py
│   ├── test_tools/
│   │   └── __init__.py
│   ├── test_safety/
│   │   └── __init__.py
│   └── fixtures/
│       └── api_responses/          # Mock API responses
│           └── .gitkeep
├── pyproject.toml
├── config.example.yaml             # Example config file (F2.2)
├── README.md
├── .env.example
├── .gitignore
└── py.typed                        # PEP 561 marker
```

### 4.2 Dependencies

```toml
[project]
name = "unifi-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",                  # MCP SDK
    "httpx>=0.27.0",               # Async HTTP client
    "pydantic>=2.0.0",             # Data validation
    "pydantic-settings>=2.0.0",    # Settings management
    "python-dotenv>=1.0.0",        # Environment variables
    "PyYAML>=6.0.0",               # YAML config file support
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",               # HTTP mocking
    "ruff>=0.3.0",                 # Linting
    "mypy>=1.9.0",                 # Type checking
]

[project.scripts]
unifi-mcp = "unifi_mcp.server:main"
```

---

## 5. Configuration

### 5.1 Configuration Schema

```python
# src/unifi_mcp/config.py
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class UniFiConfig(BaseSettings):
    """UniFi MCP Server Configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
    )

    # Connection settings
    unifi_host: str = Field(description="Controller URL (e.g., https://192.168.1.1)")
    unifi_username: str = Field(description="API username")
    unifi_password: SecretStr = Field(description="API password")
    unifi_site: str = Field(default="default", description="UniFi site name")
    unifi_verify_ssl: bool = Field(default=False, description="SSL verification")

    # Timeouts
    connection_timeout: float = Field(default=10.0, ge=1.0, le=60.0)
    request_timeout: float = Field(default=30.0, ge=5.0, le=300.0)

    # Safety settings
    dry_run: bool = Field(default=False, description="Preview mode")
    max_changes_per_minute: int = Field(default=5, ge=1, le=60)
    rollback_retention_minutes: int = Field(default=60, ge=1, le=1440)
    require_confirmation_for: list[str] = Field(
        default_factory=lambda: ["medium", "high", "critical"]
    )

    # Logging settings
    audit_log_path: str = Field(default="logs/unifi-audit.log")
    log_level: str = Field(default="INFO")
    log_to_console: bool = Field(default=True)

    # Feature flags
    enable_rollback: bool = Field(default=True)
    enable_audit_log: bool = Field(default=True)

    @property
    def api_base_url(self) -> str:
        """Get the base URL for API requests."""
        return f"{self.unifi_host}/proxy/network/api/s/{self.unifi_site}"

    @classmethod
    def from_file(cls, path: str, profile: str | None = None) -> "UniFiConfig":
        """Load configuration from YAML or JSON file with optional profile."""
        # See F2.2 for full implementation with YAML/JSON support and profiles
        ...
```

### 5.2 Environment Variables

```bash
# .env.example
UNIFI_HOST=https://192.168.1.1
UNIFI_USERNAME=claude-api
UNIFI_PASSWORD=your-secure-password
UNIFI_SITE=default
UNIFI_VERIFY_SSL=false

# Optional overrides
DRY_RUN=false
MAX_CHANGES_PER_MINUTE=5
ROLLBACK_RETENTION_MINUTES=60
AUDIT_LOG_PATH=logs/unifi-audit.log
LOG_LEVEL=INFO
```

---

## 6. UniFi API Client

### 6.1 Authentication Flow

```python
# src/client/auth.py
class UniFiAuthenticator:
    """Handles UniFi API authentication."""

    def __init__(self, config: UniFiConfig):
        self.config = config
        self._session_cookie: str | None = None
        self._csrf_token: str | None = None

    async def login(self) -> bool:
        """
        Authenticate with UniFi controller.

        POST /api/auth/login
        Body: {"username": "...", "password": "..."}
        Returns: Session cookie in Set-Cookie header
        """
        async with httpx.AsyncClient(verify=self.config.unifi_verify_ssl) as client:
            response = await client.post(
                f"{self.config.unifi_host}/api/auth/login",
                json={
                    "username": self.config.unifi_username,
                    "password": self.config.unifi_password,
                },
            )
            if response.status_code == 200:
                self._session_cookie = response.cookies.get("TOKEN")
                self._csrf_token = response.headers.get("X-CSRF-Token")
                return True
            return False

    async def logout(self) -> None:
        """End the session."""
        # POST /api/auth/logout
        pass

    @property
    def headers(self) -> dict:
        """Get headers for authenticated requests."""
        return {
            "Cookie": f"TOKEN={self._session_cookie}",
            "X-CSRF-Token": self._csrf_token,
        }
```

### 6.2 API Client

```python
# src/client/api.py
class UniFiClient:
    """Main UniFi API client."""

    def __init__(self, config: UniFiConfig):
        self.config = config
        self.auth = UniFiAuthenticator(config)
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection and authenticate."""
        self._http = httpx.AsyncClient(
            base_url=self.config.unifi_host,
            verify=self.config.unifi_verify_ssl,
            timeout=30.0,
        )
        if not await self.auth.login():
            raise AuthenticationError("Failed to authenticate with UniFi")

    async def disconnect(self) -> None:
        """Close connection."""
        await self.auth.logout()
        if self._http:
            await self._http.aclose()

    async def request(
        self,
        method: str,
        endpoint: str,
        data: dict | None = None,
    ) -> dict:
        """Make an authenticated API request."""
        url = f"/proxy/network/api/s/{self.config.unifi_site}{endpoint}"

        response = await self._http.request(
            method,
            url,
            headers=self.auth.headers,
            json=data,
        )

        if response.status_code == 401:
            # Session expired, re-authenticate
            await self.auth.login()
            response = await self._http.request(
                method, url, headers=self.auth.headers, json=data
            )

        response.raise_for_status()
        return response.json()

    # Convenience methods
    async def get(self, endpoint: str) -> dict:
        return await self.request("GET", endpoint)

    async def post(self, endpoint: str, data: dict) -> dict:
        return await self.request("POST", endpoint, data)

    async def put(self, endpoint: str, data: dict) -> dict:
        return await self.request("PUT", endpoint, data)

    async def delete(self, endpoint: str) -> dict:
        return await self.request("DELETE", endpoint)
```

### 6.3 API Endpoints Reference

| Operation | Method | Endpoint | Notes |
|-----------|--------|----------|-------|
| List clients | GET | `/stat/sta` | All connected clients |
| Get client | GET | `/stat/sta/{mac}` | Single client |
| List devices | GET | `/stat/device` | Switches, APs, etc. |
| List networks | GET | `/rest/networkconf` | VLANs/networks |
| Create network | POST | `/rest/networkconf` | New VLAN |
| Update network | PUT | `/rest/networkconf/{id}` | Modify VLAN |
| Delete network | DELETE | `/rest/networkconf/{id}` | Remove VLAN |
| List firewall rules | GET | `/rest/firewallrule` | All rulesets |
| Create firewall rule | POST | `/rest/firewallrule` | New rule |
| Update firewall rule | PUT | `/rest/firewallrule/{id}` | Modify rule |
| Delete firewall rule | DELETE | `/rest/firewallrule/{id}` | Remove rule |
| Block client | POST | `/cmd/stamgr` | `{"cmd": "block-sta", "mac": "..."}` |
| Rename client | POST | `/cmd/stamgr` | `{"cmd": "set-sta-note", ...}` |

---

## 7. Tool Definitions

### 7.1 Tool Pattern

**Note:** This project uses the FastMCP pattern for tool registration. Tools are async functions decorated with `@mcp.tool()`. See F2.9 for the full server implementation.

```python
# src/unifi_mcp/server.py - Tool registration example
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("unifi-mcp")

@mcp.tool()
async def unifi_list_networks(
    include_default: bool = True,
    vlan_only: bool = False,
) -> str:
    """
    List all networks/VLANs configured on the UniFi controller.

    Args:
        include_default: Include the default network
        vlan_only: Only return networks with VLAN IDs

    Returns:
        JSON string with network data
    """
    # Implementation calls internal functions from tools/query/networks.py
    ...
```

### 7.2 Permission Tiers

Permission tiers are defined in `safety/tiers.py`:

```python
from enum import Enum

class PermissionTier(Enum):
    READ = "read"           # Auto-approved
    LOW = "low"             # Brief confirmation
    MEDIUM = "medium"       # Detailed confirmation
    HIGH = "high"           # Explicit confirmation + rollback info
    CRITICAL = "critical"   # User-initiated only
```

### 7.3 Response Format

Tool responses use a standard JSON format via helpers:

```python
# src/unifi_mcp/tools/helpers.py
def format_success_response(
    data: dict | list,
    message: str | None = None,
    rollback_id: str | None = None,
) -> str:
    """Format successful tool response as JSON."""
    result = {"success": True, "data": data}
    if message:
        result["message"] = message
    if rollback_id:
        result["rollback_id"] = rollback_id
    return json.dumps(result, indent=2)

def format_error_response(error: str, details: dict | None = None) -> str:
    """Format error tool response as JSON."""
    result = {"success": False, "error": error}
    if details:
        result["details"] = details
    return json.dumps(result, indent=2)
```

### 7.4 Query Tools (Permission: READ)

Query tools are implemented as async functions in `tools/query/`. See F2.4 for full implementations.

#### `unifi_list_networks`

```python
# tools/query/networks.py
async def list_networks(
    client: UniFiClient,
    include_default: bool = True,
    vlan_only: bool = False,
) -> list[dict]:
    """List all networks/VLANs configured on the controller."""
    response = await client.get("/rest/networkconf")
    networks = []
    for n in response.get("data", []):
        if vlan_only and not n.get("vlan"):
            continue
        if not include_default and n.get("name") == "Default":
            continue
        networks.append({
            "id": n["_id"],
            "name": n["name"],
            "vlan_id": n.get("vlan"),
            "subnet": n.get("ip_subnet"),
            "dhcp_enabled": n.get("dhcpd_enabled", False),
            "purpose": n.get("purpose", "corporate"),
        })
    return networks
```

#### `unifi_list_clients`

```python
# tools/query/clients.py
async def list_clients(
    client: UniFiClient,
    network: str | None = None,
    wired_only: bool = False,
) -> list[dict]:
    """List all clients connected to the network."""
    response = await client.get("/stat/sta")
    clients = []
    for c in response.get("data", []):
        if network and c.get("network") != network:
            continue
        if wired_only and not c.get("is_wired", False):
            continue
        clients.append({
            "mac": c.get("mac"),
            "ip": c.get("ip"),
            "hostname": c.get("hostname"),
            "name": c.get("name") or c.get("hostname"),
            "network": c.get("network"),
            "is_wired": c.get("is_wired", False),
            "blocked": c.get("blocked", False),
        })
    return clients
```

#### `unifi_get_client`

```python
# tools/query/clients.py
async def get_client(client: UniFiClient, identifier: str) -> dict | None:
    """Get detailed information about a specific client."""
    identifier = identifier.lower()
    response = await client.get("/stat/sta")

    for c in response.get("data", []):
        if (
            c.get("mac", "").lower() == identifier
            or c.get("ip", "").lower() == identifier
            or (c.get("name") or "").lower() == identifier
            or (c.get("hostname") or "").lower() == identifier
        ):
            return {
                "mac": c.get("mac"),
                "ip": c.get("ip"),
                "hostname": c.get("hostname"),
                "name": c.get("name"),
                "oui": c.get("oui"),
                "network": c.get("network"),
                "vlan_id": c.get("vlan"),
                "is_wired": c.get("is_wired", False),
                "switch_mac": c.get("sw_mac"),
                "switch_port": c.get("sw_port"),
                "ap_mac": c.get("ap_mac"),
                "channel": c.get("channel"),
                "signal": c.get("rssi"),
                "tx_bytes": c.get("tx_bytes"),
                "rx_bytes": c.get("rx_bytes"),
                "uptime": c.get("uptime"),
                "blocked": c.get("blocked", False),
            }
    return None
```

### 7.5 Configuration Tools (Permission: MEDIUM/HIGH)

Configuration tools are implemented as async functions in `tools/config/`. See F2.5 for full implementations.

#### `unifi_create_network`

```python
# tools/config/networks.py
async def create_network(
    client: UniFiClient,
    rollback: RollbackManager,
    name: str,
    vlan_id: int,
    subnet: str,
    purpose: str = "corporate",
    dhcp_enabled: bool = True,
) -> dict:
    """
    Create a new VLAN/network.

    Args:
        name: Network name
        vlan_id: VLAN ID (2-4094)
        subnet: CIDR notation, e.g., 192.168.40.0/24
        purpose: "corporate", "guest", "vlan-only"
        dhcp_enabled: Enable DHCP server

    Returns:
        Created network data with rollback_id
    """
    # Validation
    if vlan_id < 2 or vlan_id > 4094:
        raise ValidationError("VLAN ID must be between 2 and 4094")

    # Check VLAN not in use
    existing = await client.get("/rest/networkconf")
    existing_vlans = [n.get("vlan") for n in existing.get("data", [])]
    if vlan_id in existing_vlans:
        raise ValidationError(f"VLAN ID {vlan_id} already in use")

    # Build network config
    network_config = {
        "name": name,
        "vlan": vlan_id,
        "ip_subnet": subnet,
        "dhcpd_enabled": dhcp_enabled,
        "purpose": purpose,
    }

    result = await client.post("/rest/networkconf", network_config)
    network_id = result["data"][0]["_id"]

    # Record for rollback
    rollback_id = await rollback.record(
        action="create_network",
        undo_action="delete_network",
        undo_params={"network_id": network_id},
    )

    return {
        **result["data"][0],
        "rollback_id": rollback_id,
    }
```

#### `unifi_create_firewall_rule`

```python
# tools/config/firewall.py
async def create_firewall_rule(
    client: UniFiClient,
    rollback: RollbackManager,
    name: str,
    ruleset: str,
    action: str,
    source_type: str = "any",
    destination_type: str = "any",
    protocol: str = "all",
    port: str = "any",
    enabled: bool = True,
) -> dict:
    """
    Create a new firewall rule.

    Args:
        name: Rule name
        ruleset: LAN_IN, LAN_OUT, GUEST_IN, WAN_IN, etc.
        action: accept, drop, reject
        source_type: any, network, ip, group
        destination_type: any, network, ip, group
        protocol: all, tcp, udp, tcp_udp, icmp
        port: Port or port range
        enabled: Rule enabled

    Returns:
        Created rule data with rollback_id
    """
    # Prevent overly permissive rules
    if (action == "accept"
        and source_type == "any"
        and destination_type == "any"
        and port == "any"):
        raise ValidationError("Cannot create 'allow any to any' rule")

    rule_config = {
        "name": name,
        "ruleset": ruleset,
        "action": action,
        "protocol": protocol,
        "enabled": enabled,
        # Additional source/destination config...
    }

    result = await client.post("/rest/firewallrule", rule_config)
    rule_id = result["data"][0]["_id"]

    rollback_id = await rollback.record(
        action="create_firewall_rule",
        undo_action="delete_firewall_rule",
        undo_params={"rule_id": rule_id},
    )

    return {
        **result["data"][0],
        "rollback_id": rollback_id,
    }
```

### 7.6 Complete Tool List

| Tool | Permission | Category |
|------|------------|----------|
| `unifi_list_networks` | READ | Query |
| `unifi_get_network` | READ | Query |
| `unifi_list_clients` | READ | Query |
| `unifi_get_client` | READ | Query |
| `unifi_search_clients` | READ | Query |
| `unifi_list_devices` | READ | Query |
| `unifi_get_device` | READ | Query |
| `unifi_list_firewall_rules` | READ | Query |
| `unifi_get_firewall_rule` | READ | Query |
| `unifi_get_port_status` | READ | Query |
| `unifi_get_client_on_port` | READ | Query |
| `unifi_create_network` | MEDIUM | Config |
| `unifi_update_network` | MEDIUM | Config |
| `unifi_delete_network` | HIGH | Config |
| `unifi_create_firewall_rule` | HIGH | Config |
| `unifi_delete_firewall_rule` | HIGH | Config |
| `unifi_set_port_vlan` | MEDIUM | Config |
| `unifi_rename_client` | LOW | Config |
| `unifi_block_client` | MEDIUM | Config |
| `unifi_unblock_client` | MEDIUM | Config |
| `unifi_undo` | HIGH | Rollback |

---

## 8. Safety System

### 8.1 Permission Tiers

```python
# src/safety/tiers.py
class PermissionTier(Enum):
    READ = "read"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

TIER_BEHAVIORS = {
    PermissionTier.READ: {
        "requires_confirmation": False,
        "log_level": "DEBUG",
    },
    PermissionTier.LOW: {
        "requires_confirmation": True,
        "confirmation_type": "brief",
        "log_level": "INFO",
    },
    PermissionTier.MEDIUM: {
        "requires_confirmation": True,
        "confirmation_type": "detailed",
        "log_level": "INFO",
    },
    PermissionTier.HIGH: {
        "requires_confirmation": True,
        "confirmation_type": "explicit",
        "show_rollback_info": True,
        "log_level": "WARNING",
    },
    PermissionTier.CRITICAL: {
        "requires_confirmation": True,
        "confirmation_type": "explicit",
        "user_initiated_only": True,
        "log_level": "CRITICAL",
    },
}
```

### 8.2 Validation Layer

```python
# src/safety/validation.py
class ValidationEngine:
    """Pre-execution validation for all tools."""

    async def validate(self, tool: BaseTool, params: dict) -> ValidationResult:
        """Run all validations before executing a tool."""
        errors = []
        warnings = []

        # Tool-specific validation
        if hasattr(tool, 'validate'):
            tool_errors = await tool.validate(params)
            errors.extend(tool_errors)

        # Global validations
        if tool.permission_tier == PermissionTier.HIGH:
            # Check rate limit
            if await self._rate_limit_exceeded():
                errors.append("Rate limit exceeded for write operations")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
```

### 8.3 Rollback Manager

```python
# src/safety/rollback.py
@dataclass
class RollbackEntry:
    id: str
    timestamp: datetime
    action: str
    undo_action: str
    undo_params: dict
    expires_at: datetime

class RollbackManager:
    """Manages rollback data for configuration changes."""

    def __init__(self, retention_minutes: int = 60):
        self._entries: dict[str, RollbackEntry] = {}
        self._retention = timedelta(minutes=retention_minutes)

    async def record(
        self,
        action: str,
        undo_action: str,
        undo_params: dict,
    ) -> str:
        """Record a change for potential rollback."""
        entry_id = str(uuid.uuid4())[:8]
        self._entries[entry_id] = RollbackEntry(
            id=entry_id,
            timestamp=datetime.utcnow(),
            action=action,
            undo_action=undo_action,
            undo_params=undo_params,
            expires_at=datetime.utcnow() + self._retention,
        )
        return entry_id

    async def undo(self, entry_id: str) -> ToolResult:
        """Execute rollback for a specific entry."""
        entry = self._entries.get(entry_id)
        if not entry:
            return ToolResult(success=False, error=f"Rollback entry not found: {entry_id}")

        if datetime.utcnow() > entry.expires_at:
            return ToolResult(success=False, error="Rollback entry has expired")

        # Execute the undo action
        # (dispatch to appropriate tool)

    def list_available(self) -> list[RollbackEntry]:
        """List all available rollback entries."""
        now = datetime.utcnow()
        return [e for e in self._entries.values() if e.expires_at > now]
```

---

## 9. Audit Logging

### 9.1 Log Format

```python
# src/logging/audit.py
@dataclass
class AuditLogEntry:
    timestamp: str
    tool: str
    permission_tier: str
    parameters: dict
    result: str  # "success" | "failure" | "validation_error"
    message: str | None
    error: str | None
    rollback_id: str | None
    duration_ms: int

class AuditLogger:
    """Logs all tool executions for audit trail."""

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    async def log(self, entry: AuditLogEntry) -> None:
        """Append entry to audit log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
```

### 9.2 Sample Log Output

```json
{"timestamp": "2025-01-09T15:30:00Z", "tool": "unifi_create_network", "permission_tier": "medium", "parameters": {"name": "IoT-Media", "vlan_id": 40, "subnet": "192.168.40.0/24"}, "result": "success", "message": "Created network 'IoT-Media' (VLAN 40)", "rollback_id": "a1b2c3d4", "duration_ms": 342}
{"timestamp": "2025-01-09T15:31:00Z", "tool": "unifi_create_firewall_rule", "permission_tier": "high", "parameters": {"name": "Allow IoT to NAS", "action": "accept"}, "result": "success", "rollback_id": "e5f6g7h8", "duration_ms": 287}
```

---

## 10. MCP Server Implementation

### 10.1 Server Entry Point

Uses FastMCP for a clean, decorator-based approach to tool registration. See F2.9 for full implementation.

```python
# src/unifi_mcp/server.py
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

from unifi_mcp.config import UniFiConfig
from unifi_mcp.config_loader import get_config
from unifi_mcp.client import UniFiClient
from unifi_mcp.tools.helpers import format_success_response, format_error_response

# Global state managed by lifespan
_client: UniFiClient | None = None
_config: UniFiConfig | None = None

@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage UniFi client connection lifecycle."""
    global _client, _config

    _config = get_config()
    _client = UniFiClient(_config)
    await _client.connect()

    try:
        yield
    finally:
        await _client.disconnect()
        _client = None

mcp = FastMCP("unifi-mcp", lifespan=lifespan)

@mcp.tool()
async def unifi_list_networks(
    include_default: bool = True,
    vlan_only: bool = False,
) -> str:
    """List all networks/VLANs configured on the UniFi controller."""
    from unifi_mcp.tools.query.networks import list_networks

    networks = await list_networks(_client, include_default, vlan_only)
    return format_success_response(networks)

@mcp.tool()
async def unifi_list_clients(
    network: str | None = None,
    wired_only: bool = False,
) -> str:
    """List all clients connected to the network."""
    from unifi_mcp.tools.query.clients import list_clients

    clients = await list_clients(_client, network, wired_only)
    return format_success_response(clients)

# ... additional tools registered via @mcp.tool() ...

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
```

### 10.2 Claude Code Configuration

```json
// .claude/settings.json
{
  "mcpServers": {
    "unifi": {
      "command": "python",
      "args": ["-m", "unifi_mcp.server"],
      "cwd": "/path/to/mcp-servers/unifi-mcp",
      "env": {
        "UNIFI_HOST": "https://192.168.1.1",
        "UNIFI_USERNAME": "claude-api",
        "UNIFI_PASSWORD": "${UNIFI_PASSWORD}",
        "UNIFI_SITE": "default"
      }
    }
  }
}
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

```python
# tests/test_tools/test_query.py
import pytest
from respx import MockRouter

from unifi_mcp.config import UniFiConfig
from unifi_mcp.client import UniFiClient
from unifi_mcp.tools.query.networks import list_networks

@pytest.fixture
def mock_unifi_api(respx_mock: MockRouter):
    """Mock UniFi API responses."""
    respx_mock.post("/api/auth/login").respond(
        json={"meta": {"rc": "ok"}},
        headers={"Set-Cookie": "TOKEN=test123"},
    )
    respx_mock.get("/proxy/network/api/s/default/rest/networkconf").respond(
        json={
            "meta": {"rc": "ok"},
            "data": [
                {"_id": "abc123", "name": "Default", "vlan": 1},
                {"_id": "def456", "name": "IoT", "vlan": 10},
            ],
        }
    )
    return respx_mock

@pytest.mark.asyncio
async def test_list_networks(mock_unifi_api, config):
    async with UniFiClient(config) as client:
        networks = await list_networks(client, include_default=True)

    assert len(networks) == 2
    assert networks[0]["vlan_id"] == 1
```

### 11.2 Integration Tests

```python
# tests/integration/test_live_api.py
import os
import pytest

from unifi_mcp.config import UniFiConfig
from unifi_mcp.client import UniFiClient
from unifi_mcp.tools.query.networks import list_networks

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("UNIFI_INTEGRATION"), reason="Integration disabled")
class TestLiveUniFiAPI:
    """Test against real UniFi controller (read-only operations)."""

    @pytest.mark.asyncio
    async def test_list_networks_live(self):
        config = UniFiConfig()  # From environment
        async with UniFiClient(config) as client:
            networks = await list_networks(client)
        assert isinstance(networks, list)
```

### 11.3 Test Fixtures

Store sample API responses in `tests/fixtures/api_responses/`:
- `clients.json`
- `networks.json`
- `firewall_rules.json`
- `devices.json`

---

## 12. Error Handling

### 12.1 Error Types

```python
# src/errors.py
class UniFiMCPError(Exception):
    """Base exception for UniFi MCP server."""
    pass

class AuthenticationError(UniFiMCPError):
    """Failed to authenticate with UniFi."""
    pass

class ValidationError(UniFiMCPError):
    """Pre-execution validation failed."""
    pass

class APIError(UniFiMCPError):
    """UniFi API returned an error."""
    pass

class RateLimitError(UniFiMCPError):
    """Rate limit for write operations exceeded."""
    pass
```

### 12.2 Error Responses

All errors are returned as `ToolResult` with `success=False`:

```python
ToolResult(
    success=False,
    error="Validation failed: VLAN ID 10 already in use",
)
```

---

## 13. Interfaces

### 13.1 Input: Documentation Corpus (Feature 1)

The MCP server doesn't directly depend on the crawler at runtime, but uses the corpus during development to understand API shapes.

### 13.2 Output: To Claude Code Integration (Feature 3)

Feature 3 (Skills, Workflows) will build on top of this MCP server:
- Skills call multiple tools in sequence
- Workflows coordinate complex multi-step operations
- Slash commands trigger workflows

---

## 14. Open Questions

- [ ] How to handle UniFi API rate limits (if any)?
- [ ] Support for multiple sites?
- [ ] WebSocket for real-time updates?
- [ ] Backup config before any changes?

---

## 15. Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| F2.1 | Project setup | Directory structure, dependencies |
| F2.2 | Configuration | Settings management, env vars |
| F2.3 | API client | Auth, session, basic requests |
| F2.4 | Query tools | All read-only tools |
| F2.5 | Config tools | VLAN, firewall, port tools |
| F2.6 | Safety system | Validation, tiers, rate limiting |
| F2.7 | Rollback system | Undo capability |
| F2.8 | Audit logging | Comprehensive logging |
| F2.9 | MCP integration | Server running, tools exposed |
| F2.10 | Testing | Unit + integration tests |
| F2.11 | Documentation | README, usage examples |

---

*Document Version: 1.1*
*Last Updated: 2026-01-10*
*Changes: Updated to align with task files - FastMCP pattern, network naming, extended config*
