# Phase 3: Home Automation Integration

Detailed specification for building the Home Assistant MCP server and smart home tooling.

**Parent Document:** [masteridea.md](./masteridea.md)
**Prerequisites:** Phase 1 (UniFi), Phase 2 (Proxmox) complete
**Status:** Planning - Awaiting Research
**Target Platform:** Home Assistant

---

## Features Overview

Phase 3 consists of four features:

| Feature | Name | Spec Document | Description |
|---------|------|---------------|-------------|
| F1 | Documentation & Research | [phase3-f1-documentation-research.md](./phase3-f1-documentation-research.md) | Gathers Home Assistant API docs and establishes project foundation |
| F2 | Home Assistant MCP Server | [phase3-f2-ha-mcp-server.md](./phase3-f2-ha-mcp-server.md) | Exposes Home Assistant API as MCP tools |
| F3 | Claude Code Integration | [phase3-f3-claude-code-integration.md](./phase3-f3-claude-code-integration.md) | Skills, slash commands, hooks |
| F4 | SubAgent Integration | [phase3-f4-subagent-integration.md](./phase3-f4-subagent-integration.md) | Specialized autonomous agents for home automation analysis |

**See individual feature specifications for detailed requirements.**

---

## 1. Prerequisites

### 1.1 Home Assistant Setup

Before implementation, document your Home Assistant ecosystem:

```yaml
# To be filled in during research phase
home_assistant:
  host: ""                    # e.g., 192.168.1.20:8123
  version: ""                 # e.g., 2024.1.0
  installation_type: ""       # OS, Container, Supervised, Core

areas:
  - name: ""
    device_count: 0

integrations:
  - name: ""
    platform: ""
    device_count: 0
    entity_count: 0

device_summary:
  lights: 0
  switches: 0
  sensors: 0
  climate: 0
  locks: 0
  covers: 0
  media_players: 0
  cameras: 0
```

### 1.2 API Access Setup

**Step 1: Create Long-Lived Access Token**
```
Profile → Long-Lived Access Tokens → Create Token
Name: claude-infrastructure
```

**Step 2: Document token**
```
Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Step 3: Verify access**
```bash
curl -H "Authorization: Bearer TOKEN" \
  http://{HA_HOST}:8123/api/
```

**Step 4: Discover API capabilities**
- Review REST API documentation
- Test WebSocket connection
- Note available services per domain

### 1.3 Automation Baseline

Document current automation state before making any changes:

| Item | Current Value | Notes |
|------|---------------|-------|
| Total automations | | Baseline count |
| Active scenes | | Scene count |
| Script count | | Helper scripts |
| Entity count | | Total entities |
| Critical devices | | Never auto-control |

---

## 2. Documentation Corpus

### 2.1 Documentation Sources

| Source | URL Pattern | Content Type | Priority |
|--------|-------------|--------------|----------|
| Official Docs | `developers.home-assistant.io/*` | HTML | High |
| REST API | `developers.home-assistant.io/docs/api/rest/` | HTML | High |
| WebSocket API | `developers.home-assistant.io/docs/api/websocket/` | HTML | High |
| Integrations | `www.home-assistant.io/integrations/*` | HTML | Medium |
| Community | `community.home-assistant.io/*` | HTML | Low |

### 2.2 Local Exports

From your Home Assistant instance, export:

| Export | Location/Method | Format | Purpose |
|--------|-----------------|--------|---------|
| Config backup | Settings → Backups | tar.gz | Full config reference |
| Entity registry | Developer Tools → States | JSON | Current entity list |
| Automation list | Settings → Automations | YAML | Automation inventory |
| Scene list | Settings → Scenes | YAML | Scene inventory |

### 2.3 Output Structure

```
ai_docs/vendor/home-assistant/
├── versions.yaml           # Version tracking
├── api/
│   ├── rest-api.md         # REST API documentation
│   ├── websocket-api.md    # WebSocket API documentation
│   ├── services.md         # Available services by domain
│   ├── events.md           # Event types
│   └── examples/           # Request/response examples
├── domains/
│   ├── light.md            # Light domain specifics
│   ├── switch.md           # Switch domain
│   ├── climate.md          # Climate/HVAC
│   ├── lock.md             # Lock domain
│   ├── cover.md            # Cover domain
│   └── [other domains]
└── local-exports/
    ├── entity-registry.json
    ├── automations.yaml
    └── scenes.yaml
```

---

## 3. MCP Server: `ha-mcp`

### 3.1 Project Structure

See [phase3-f2-ha-mcp-server.md](./phase3-f2-ha-mcp-server.md) for the detailed project structure.

**Key points:**
- Uses **FastMCP pattern** with `@mcp.tool()` decorators for tool registration
- Tools defined inline in `server.py`, logic in `tools/query/` and `tools/control/` subdirectories
- Separate `safety/` module for domain-specific risk assessment
- WebSocket client for real-time state updates

```
mcp-servers/ha-mcp/
├── src/ha_mcp/
│   ├── server.py               # MCP server with FastMCP
│   ├── config.py               # Configuration management
│   ├── client/                 # Home Assistant API client
│   │   ├── rest.py             # REST API client
│   │   └── websocket.py        # WebSocket client
│   ├── tools/                  # Tool implementations
│   │   ├── query/              # State query tools
│   │   ├── control/            # Device control tools
│   │   └── automation/         # Automation tools
│   ├── models/                 # Data models
│   │   ├── entity.py
│   │   ├── state.py
│   │   └── service.py
│   ├── safety/                 # Domain-specific validation
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
name = "ha-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",              # MCP SDK
    "httpx>=0.27.0",           # Async HTTP client
    "websockets>=12.0",        # WebSocket client
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

class HAConfig(BaseSettings):
    """Configuration loaded from environment."""

    ha_host: str                       # http://192.168.1.20:8123
    ha_token: str                      # Long-lived access token
    ha_verify_ssl: bool = True

    # WebSocket settings
    ws_enabled: bool = True            # Enable real-time updates
    ws_reconnect_interval: int = 5     # Seconds

    # Safety settings
    dry_run: bool = False              # Preview mode
    require_confirmation: bool = True  # For critical domains
    protected_entities: list[str] = [] # Never auto-control
    max_changes_per_minute: int = 10   # Rate limit

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
| `ha_list_entities` | List all entities, optionally filtered by domain/area |
| `ha_get_state` | Get current state of entity |
| `ha_list_areas` | List defined areas/rooms |
| `ha_list_devices` | List devices |
| `ha_list_scenes` | List available scenes |
| `ha_list_automations` | List automations |
| `ha_get_history` | Get state history for entity |
| `ha_list_services` | List available services by domain |
| `ha_get_config` | Get Home Assistant configuration info |

### 4.2 Control Tools - Low Risk Domains

| Tool | Description | Domains |
|------|-------------|---------|
| `ha_turn_on` | Turn on entity | light, switch, fan, media_player |
| `ha_turn_off` | Turn off entity | light, switch, fan, media_player |
| `ha_toggle` | Toggle entity state | light, switch, fan |
| `ha_set_brightness` | Set light brightness | light |
| `ha_set_color` | Set light color | light |
| `ha_set_volume` | Set media player volume | media_player |
| `ha_media_control` | Play/pause/stop media | media_player |

### 4.3 Control Tools - Medium Risk Domains

| Tool | Description | Risk |
|------|-------------|------|
| `ha_set_temperature` | Set thermostat temperature | Medium |
| `ha_set_hvac_mode` | Set heating/cooling mode | Medium |
| `ha_set_cover_position` | Set cover/blind position | Medium |
| `ha_activate_scene` | Activate a scene | Medium |
| `ha_call_service` | Call any HA service | Medium |

### 4.4 Control Tools - High Risk Domains (Require Confirmation)

| Tool | Description | Risk |
|------|-------------|------|
| `ha_lock` | Lock a lock entity | High |
| `ha_unlock` | Unlock a lock entity | High |
| `ha_arm_alarm` | Arm alarm panel | High |
| `ha_disarm_alarm` | Disarm alarm panel | High |
| `ha_open_garage` | Open garage door | High |
| `ha_close_garage` | Close garage door | High |

### 4.5 Automation Tools (Require Confirmation)

| Tool | Description | Risk |
|------|-------------|------|
| `ha_enable_automation` | Enable automation | Low |
| `ha_disable_automation` | Disable automation | Low |
| `ha_trigger_automation` | Manually trigger | Medium |
| `ha_create_automation` | Create new automation | High |
| `ha_delete_automation` | Delete automation | High |
| `ha_update_automation` | Modify automation | High |

### 4.6 Complete Tool Summary

| Category | Tools |
|----------|-------|
| **Query (READ)** | `ha_list_entities`, `ha_get_state`, `ha_list_areas`, `ha_list_devices`, `ha_list_scenes`, `ha_list_automations`, `ha_get_history`, `ha_list_services`, `ha_get_config` |
| **Control (LOW)** | `ha_turn_on`, `ha_turn_off`, `ha_toggle`, `ha_set_brightness`, `ha_set_color`, `ha_set_volume`, `ha_media_control`, `ha_enable_automation`, `ha_disable_automation` |
| **Control (MEDIUM)** | `ha_set_temperature`, `ha_set_hvac_mode`, `ha_set_cover_position`, `ha_activate_scene`, `ha_call_service`, `ha_trigger_automation` |
| **Control (HIGH)** | `ha_lock`, `ha_unlock`, `ha_arm_alarm`, `ha_disarm_alarm`, `ha_open_garage`, `ha_close_garage`, `ha_create_automation`, `ha_delete_automation`, `ha_update_automation` |

---

## 5. Entity Domain Handling

### 5.1 Supported Domains

| Domain | Read | Write | Risk Level | Notes |
|--------|------|-------|------------|-------|
| `light` | Yes | Yes | Low | On/off, brightness, color |
| `switch` | Yes | Yes | Low | On/off |
| `fan` | Yes | Yes | Low | On/off, speed |
| `climate` | Yes | Yes | Medium | Temperature, mode |
| `cover` | Yes | Yes | Medium | Open/close, position |
| `lock` | Yes | Confirm | High | Lock/unlock |
| `alarm_control_panel` | Yes | Confirm | High | Arm/disarm |
| `media_player` | Yes | Yes | Low | Play, pause, volume |
| `sensor` | Yes | No | Read | Temperature, humidity, etc. |
| `binary_sensor` | Yes | No | Read | Motion, door, etc. |
| `camera` | Yes | No | Read | Snapshot URL |
| `vacuum` | Yes | Yes | Low | Start, stop, dock |
| `garage_door` | Yes | Confirm | High | Open/close |

### 5.2 Safety Considerations by Domain

**Auto-approved control:**
- Lights (non-critical)
- Switches (non-critical appliances)
- Media players
- Fans
- Vacuums

**Require confirmation:**
- Locks
- Alarm panels
- Garage doors
- Critical climate changes (extreme temperatures)

---

## 6. Orchestration Layer

This section provides a high-level overview. See feature specifications for detailed implementations:
- **Feature 3:** [phase3-f3-claude-code-integration.md](./phase3-f3-claude-code-integration.md) - Skills, Commands, Hooks
- **Feature 4:** [phase3-f4-subagent-integration.md](./phase3-f4-subagent-integration.md) - SubAgents for complex analysis

### 6.1 Native Skill System

Skills use **Claude Code's native skill system** - markdown instruction files in `.claude/skills/` that Claude follows when activated.

**Core Skills:**
| Skill | Purpose |
|-------|---------|
| `home-automation` | Core device control and state queries |
| `scene-management` | Scene activation and creation workflows |
| `automation-control` | Automation management and troubleshooting |

### 6.2 Slash Commands

Commands in `.claude/commands/` provide explicit, user-invoked workflows:

| Command | Description |
|---------|-------------|
| `/ha-status` | Show home status overview |
| `/ha-lights` | Control lights by area |
| `/ha-climate` | Manage thermostats |
| `/ha-scene` | Activate or list scenes |
| `/ha-away` | Set away mode |
| `/ha-goodnight` | Activate bedtime routine |
| `/ha-find` | Find entity by name |
| `/ha-history` | Query entity history |

### 6.3 SubAgents (Feature 4)

Specialized autonomous agents for complex analysis tasks:

| Agent | Purpose |
|-------|---------|
| **Scene Designer** | Create and optimize scenes based on user preferences |
| **Automation Advisor** | Suggest automations based on usage patterns |
| **Energy Analyzer** | Analyze energy consumption patterns |
| **Presence Coordinator** | Coordinate presence-based automations with network |

SubAgents operate read-only and produce **Execution Plans** for user review.

### 6.4 Hooks

Event-driven shell scripts in `.claude/hooks/` for validation and logging:

| Hook | Purpose |
|------|---------|
| `pre-lock-change.sh` | Requires explicit confirmation for lock operations |
| `pre-alarm-change.sh` | Validates alarm state changes |
| `post-change-log.sh` | Logs all device state changes |

---

## 7. Real-Time Updates

### 7.1 WebSocket Connection

Home Assistant supports WebSocket for real-time state updates:

```python
async def subscribe_to_states(callback):
    """Subscribe to all state changes via WebSocket."""
    async with websockets.connect(f"ws://{HA_HOST}/api/websocket") as ws:
        # Authenticate
        await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))

        # Subscribe to state changes
        await ws.send(json.dumps({
            "id": 1,
            "type": "subscribe_events",
            "event_type": "state_changed"
        }))

        async for message in ws:
            event = json.loads(message)
            if event.get("type") == "event":
                await callback(event["event"])
```

### 7.2 Use Cases for Real-Time

- Notify when motion detected
- Alert when door unlocked
- Update when device state changes
- Integration with Claude Code hooks
- Cross-system presence detection

---

## 8. Cross-System Integration

### 8.1 UniFi + Home Assistant

| Scenario | Integration |
|----------|-------------|
| Presence detection | UniFi client connection → HA presence |
| Guest arrival | UniFi guest connects → HA welcomes |
| Device offline | HA device unavailable → Check UniFi for network issue |
| Network isolation | HA IoT devices on dedicated UniFi VLAN |

### 8.2 Proxmox + Home Assistant

| Scenario | Integration |
|----------|-------------|
| HA runs in Proxmox | VM/Container status affects HA availability |
| Resource monitoring | HA sensor for Proxmox node stats |
| Backup coordination | Snapshot HA VM before major changes |

### 8.3 Shared Orchestration Example

**"I'm having a party":**
1. (UniFi) Enable guest WiFi with custom password
2. (HA) Set "Party" scene (lights, music)
3. (HA) Disable motion-based automations
4. (HA) Set thermostat slightly lower (more people = more heat)
5. Report: "Guest WiFi: PartyTime / Password: welcome123"

---

## 9. Safety Model

### 9.1 Permission Tiers

| Tier | Operations | Behavior |
|------|-----------|----------|
| **Read** | Query, list, get | Auto-approved |
| **Low** | Lights, switches, fans, media | Auto-approved |
| **Medium** | Climate, covers, scenes | Brief confirmation |
| **High** | Locks, alarms, garage doors | Explicit confirmation |
| **Critical** | Automation creation/deletion | User-initiated only |

### 9.2 Guardrails

- Never unlock locks without explicit confirmation
- Never disarm alarms without explicit confirmation
- Respect protected_entities list
- Validate temperature ranges for climate control
- Max 10 changes per minute
- All changes logged to audit trail

---

## 10. Testing Strategy

### 10.1 Unit Tests

Mock Home Assistant API responses for all tool tests:

```python
# tests/test_tools_query.py
import pytest
from respx import MockRouter

@pytest.fixture
def mock_ha(respx_mock: MockRouter):
    respx_mock.get("/api/states").respond(json=[
        {"entity_id": "light.living_room", "state": "on", ...}
    ])
    return respx_mock

async def test_list_entities(mock_ha, ha_client):
    entities = await ha_client.list_entities()
    assert len(entities) >= 1
    assert entities[0].entity_id == "light.living_room"
```

### 10.2 Integration Tests

Run against real Home Assistant in controlled conditions.

### 10.3 Dry Run Mode

All control tools support `dry_run=True`.

---

## 11. Milestones

Phase 3 milestones are tracked at the feature level. See individual specifications for detailed task breakdowns.

### Feature 1: Documentation & Research
| ID | Milestone |
|----|-----------|
| F1.1 | Project setup |
| F1.2 | REST API documentation gathering |
| F1.3 | WebSocket API documentation |
| F1.4 | Domain-specific service documentation |
| F1.5 | Local environment documentation |

### Feature 2: Home Assistant MCP Server
| ID | Milestone |
|----|-----------|
| F2.1 | Project setup |
| F2.2 | Configuration management |
| F2.3 | REST API client |
| F2.4 | WebSocket client |
| F2.5 | Query tools implemented |
| F2.6 | Control tools - Low risk domains |
| F2.7 | Control tools - Medium risk domains |
| F2.8 | Control tools - High risk domains |
| F2.9 | Automation tools |
| F2.10 | Safety system |
| F2.11 | Audit logging |
| F2.12 | Testing and documentation |

### Feature 3: Claude Code Integration
| ID | Milestone |
|----|-----------|
| F3.1 | Project setup |
| F3.2 | Core skills |
| F3.3 | Slash commands |
| F3.4 | Hooks configuration |
| F3.5 | Cross-system skills (UniFi + Proxmox integration) |
| F3.6 | Testing and documentation |

### Feature 4: SubAgent Integration
| ID | Milestone |
|----|-----------|
| F4.1 | Project setup |
| F4.2 | Core agent framework |
| F4.3 | Scene Designer agent |
| F4.4 | Automation Advisor agent |
| F4.5 | Energy Analyzer agent |
| F4.6 | Presence Coordinator agent |
| F4.7 | Agent-to-skill integration |
| F4.8 | Testing and documentation |

See individual feature specifications for complete milestone details.

---

## 12. Open Questions

*To be resolved during research phase:*

- [ ] Which Home Assistant installation type do you use?
- [ ] What integrations/device types are most important?
- [ ] Is real-time monitoring desired or query-only?
- [ ] Any specific automations to expose?
- [ ] Security constraints (e.g., never unlock doors)?
- [ ] Which entities should be in the protected list?

---

## 13. Research Tasks

*Documentation to gather:*

- [ ] Home Assistant REST API documentation
- [ ] WebSocket API for real-time updates
- [ ] Service call patterns for each domain
- [ ] Area and device organization patterns
- [ ] Automation schema and YAML format
- [ ] Best practices for API token management
- [ ] Rate limiting and connection pooling
- [ ] Entity naming conventions

---

*Document Version: 2.0*
*Last Updated: 2026-01-11*
*Changelog: v2.0 - Restructured to match Phase 1 format with Features Overview (F1-F4), updated tool organization with risk tiers, added orchestration layer, aligned milestones with feature specs*
