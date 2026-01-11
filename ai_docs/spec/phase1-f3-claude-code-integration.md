# Phase 1 - Feature 3: Claude Code Integration

Skills, workflows, slash commands, and hooks that orchestrate UniFi operations through Claude Code.

**Parent Document:** [phase1-unifi.md](./phase1-unifi.md)
**Dependencies:**
- Feature 2 (UniFi MCP Server) - provides the underlying tools
**Status:** Planning

---

## 1. Purpose

### 1.1 What This Feature Does

While Feature 2 (MCP Server) provides atomic tools for UniFi operations, Feature 3 builds the **orchestration layer**:

- **Skills:** Reusable prompt templates that combine multiple tools
- **Slash Commands:** User-facing shortcuts to invoke workflows
- **Hooks:** Event-driven notifications and automations
- **Confirmation Flows:** Safety UX for multi-step operations

### 1.2 Why This Layer Matters

Raw MCP tools are powerful but low-level. Users shouldn't need to know:
- Which specific tools to call
- What order to call them
- How to handle intermediate results
- Error recovery strategies

This layer provides **intent-based interfaces**:
> "Isolate my TV to a new VLAN" → decomposed into correct tool sequence automatically

### 1.3 Scope

| In Scope | Out of Scope |
|----------|--------------|
| UniFi-specific skills | Cross-system workflows (Phase 2+) |
| Slash commands for common operations | Web UI for management |
| Confirmation flows | Custom skill builder |
| Completion hooks | Real-time monitoring dashboard |
| Error handling and recovery | |

---

## 2. Architecture

### 2.1 Layer Relationship

This feature uses **Claude Code's native extensibility system**, not a custom engine:

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                 │
│                          │                                   │
│    "Isolate my TV"   or  /infra-isolate TV                  │
│                          │                                   │
└──────────────────────────┼──────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────┐
│         Feature 3: Claude Code Integration                   │
├──────────────────────────┼──────────────────────────────────┤
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Claude Code Native System                   │   │
│  │   • Skills (.claude/skills/) - auto-activated        │   │
│  │   • Commands (.claude/commands/) - /slash invoked    │   │
│  │   • Hooks (.claude/hooks/) - event-driven scripts    │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │                   Claude AI                           │   │
│  │   • Reads skill/command instructions                 │   │
│  │   • Follows documented patterns                      │   │
│  │   • Builds confirmation prompts                      │   │
│  │   • Handles errors per safety rules                  │   │
│  └────────────────────────┬─────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │                Hook Scripts                           │   │
│  │   • PreToolUse → validate, block dangerous ops       │   │
│  │   • PostToolUse → log changes, notify                │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│         Feature 2: UniFi MCP Server                          │
│                           │                                  │
│    unifi_list_clients, unifi_create_network, etc.           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Location | Purpose |
|-----------|----------|---------|
| **Skills** | `.claude/skills/*/SKILL.md` | Auto-activated instruction sets for Claude |
| **Slash Commands** | `.claude/commands/*.md` | User-invoked workflows with argument parsing |
| **Hooks** | `.claude/hooks/*.sh` + `settings.json` | Event-driven shell scripts for validation/logging |
| **CLAUDE.md** | Project root | Always-loaded project context |

---

## 3. Skills System

Skills use **Claude Code's native skill system** - markdown instruction files that Claude follows when activated by context-matching queries.

### 3.1 Skill Definition Format

Skills are markdown files with YAML frontmatter in `.claude/skills/`:

```markdown
---
name: unifi-infrastructure
description: |
  Manages UniFi network infrastructure including VLANs, firewall rules,
  switch ports, and client management. Activates when user asks about
  network configuration, device isolation, or firewall rules.
allowed-tools: mcp__unifi__*, Read, Grep, Glob
---

# UniFi Infrastructure Management Skill

You are an expert network administrator managing a UniFi-based homelab.

## Available MCP Tools

### Query Tools (Safe - Use Freely)
| Tool | Purpose |
|------|---------|
| `unifi_list_networks` | List all VLANs/networks |
| `unifi_get_client` | Get client by name, MAC, or IP |
| ...

### Configuration Tools (Require Confirmation)
| Tool | Risk Level |
|------|------------|
| `unifi_create_network` | MEDIUM |
| `unifi_create_firewall_rule` | HIGH |
| ...

## Workflow Patterns

### Pattern 1: Device Isolation
When a user wants to isolate a device:
1. Find the device with `unifi_get_client`
2. List existing networks with `unifi_list_networks`
3. Calculate VLAN ID and subnet
4. Present change plan to user
5. After confirmation: create network, configure port, create rules
6. Report results with rollback IDs

## Safety Rules
See SAFETY.md for prohibited actions.
```

### 3.2 Skill Directory Structure

```
.claude/
├── skills/
│   ├── unifi-infra/
│   │   ├── SKILL.md      # Main skill definition
│   │   ├── PATTERNS.md   # Reusable workflow patterns
│   │   └── SAFETY.md     # Safety rules and prohibitions
│   ├── guest-network/
│   │   └── SKILL.md
│   └── security-audit/
│       └── SKILL.md
├── commands/
│   └── *.md              # Slash commands
├── hooks/
│   └── *.sh              # Hook scripts
└── settings.json         # Hook configuration
```

### 3.3 How Skills Work

Skills are **instruction documents** - Claude reads and follows them when activated:

1. **Activation**: Skill auto-activates when user query matches the `description` in frontmatter
2. **Execution**: Claude follows the documented patterns and uses listed MCP tools
3. **Confirmation**: Claude builds change plans per skill instructions and awaits user approval
4. **Safety**: Claude follows safety rules documented in SAFETY.md

No custom Python engine is needed - Claude handles orchestration natively.

### 3.4 Core Skills Catalog

| Skill | Description | Location |
|-------|-------------|----------|
| `unifi-infra` | Core infrastructure management (isolation, finding, blocking) | `.claude/skills/unifi-infra/` |
| `guest-network` | Guest WiFi creation with isolation | `.claude/skills/guest-network/` |
| `security-audit` | Network security analysis | `.claude/skills/security-audit/` |

---

## 4. Slash Commands

Slash commands are markdown files in `.claude/commands/` that provide explicit, user-invoked workflows.

### 4.1 Command Definition Format

Commands are markdown files with YAML frontmatter:

```markdown
---
description: Isolate a device to its own VLAN with optional access rules
allowed-tools: mcp__unifi__*
argument-hint: <device> [--vlan-name <name>] [--allow <targets>]
---

# /infra-isolate

Isolate a network device to a dedicated VLAN.

## Arguments
- `device` (required): Device name, MAC, or IP
- `--vlan-name <name>`: Custom VLAN name
- `--allow <targets>`: Comma-separated devices to allow access to

## Workflow
1. Find device with `unifi_get_client`
2. Survey existing networks
3. Present change plan
4. Execute after confirmation
5. Report results with rollback IDs
```

### 4.2 Available Commands

| Command | Description | Arguments |
|---------|-------------|-----------|
| `/infra-isolate` | Isolate device to own VLAN | `<device> [--vlan-name] [--vlan-id] [--allow]` |
| `/infra-find` | Find device connection details | `<device>` |
| `/infra-block` | Block device from network | `<device>` |
| `/infra-unblock` | Unblock a blocked device | `<device>` |
| `/infra-status` | Show network overview | `[--section <name>]` |
| `/infra-undo` | Undo recent changes | `[--list] [--id <id>]` |
| `/security-audit` | Run security audit | `[--deep] [--focus <area>]` |
| `/infra-guest` | Create guest network | `[--name] [--hours] [--password]` |
| `/infra-unknown` | List unnamed devices | - |
| `/infra-rename` | Rename a device | `<mac> <new-name>` |

### 4.3 Usage Examples

```bash
# Isolate a device
/infra-isolate "Living Room TV" --vlan-name "Media-IoT" --allow "NAS"

# Find where a device is connected
/infra-find "aa:bb:cc:dd:ee:ff"

# Quick security audit
/security-audit

# Deep security audit with SubAgent
/security-audit --deep --focus firewall

# Block a device
/infra-block "suspicious-device"

# Undo last change
/infra-undo --list
/infra-undo --id 3

# Create guest network
/infra-guest "Party WiFi" --hours 24
```

---

## 5. Confirmation Flows

Skills and commands instruct Claude to present change plans before executing configuration changes.

### 5.1 Change Plan Format

For multi-step operations, Claude presents a clear change plan:

```markdown
## Device Isolation Plan

**Device:** Living Room TV (aa:bb:cc:dd:ee:01)
**Current Network:** Default
**Risk Level:** Medium

### Planned Changes:

1. **Create Network/VLAN**
   - Name: TV_Isolated
   - VLAN ID: 100
   - Subnet: 192.168.100.0/24
   - DHCP: Enabled (.10 - .250)
   - Risk: MEDIUM

2. **Configure Switch Port**
   - Switch: Office Switch
   - Port: 5
   - Change: Native VLAN Default → VLAN 100
   - Risk: MEDIUM
   - Note: Device will briefly lose connectivity

3. **Create Allow Rule**
   - Allow TV_Isolated → NAS (192.168.1.50)
   - Risk: HIGH

4. **Create Isolation Rule**
   - Block TV_Isolated → All RFC1918
   - Risk: HIGH

### After Completion:
- Device will have new IP in 192.168.100.x
- All changes can be undone with `/infra-undo`

**Proceed with this isolation?** [Yes/No]
```

### 5.2 Confirmation Behavior

Claude handles confirmation natively per skill instructions:

1. **Present plan** in markdown format
2. **Wait for explicit confirmation** ("yes", "y", "proceed")
3. **Allow modifications** if user requests changes
4. **Execute or cancel** based on response
5. **Report rollback IDs** for undo capability

---

## 6. Hooks System

Hooks are **shell scripts** triggered by Claude Code events, configured in `.claude/settings.json`.

### 6.1 Hook Event Types

| Event | When Triggered | Can Block |
|-------|---------------|-----------|
| `PreToolUse` | Before MCP tool execution | Yes (exit non-zero) |
| `PostToolUse` | After MCP tool execution | No |

### 6.2 Hook Configuration

Hooks are registered in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__unifi__unifi_delete_network",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pre-delete-network.sh"
          }
        ]
      },
      {
        "matcher": "mcp__unifi__unifi_create_firewall_rule",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/pre-firewall-rule.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "mcp__unifi__unifi_create_*|mcp__unifi__unifi_delete_*|mcp__unifi__unifi_update_*",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/post-change-log.sh"
          }
        ]
      }
    ]
  }
}
```

### 6.3 Hook Scripts

Hooks receive JSON on stdin with tool context:

```bash
#!/usr/bin/env bash
# .claude/hooks/pre-delete-network.sh
# Blocks deletion of protected networks

INPUT=$(cat)
IDENTIFIER=$(echo "$INPUT" | jq -r '.tool_input.identifier // ""')

PROTECTED=("default" "lan" "management")
for net in "${PROTECTED[@]}"; do
    if [[ "${IDENTIFIER,,}" == "$net" ]]; then
        echo "BLOCKED: Cannot delete protected network '$IDENTIFIER'"
        exit 1  # Block the operation
    fi
done

exit 0  # Allow the operation
```

### 6.4 Configured Hooks

| Hook | Purpose |
|------|---------|
| `pre-delete-network.sh` | Blocks deletion of protected networks |
| `pre-firewall-rule.sh` | Blocks dangerous firewall rules (allow any-to-any) |
| `post-change-log.sh` | Logs all configuration changes to audit trail |
| `high-risk-notify.sh` | Logs high-risk operations separately |

---

## 7. Error Handling and Recovery

### 7.1 Error Scenarios

| Scenario | Handling |
|----------|----------|
| Tool fails mid-workflow | Report failure, offer `/infra-undo` for partial changes |
| Validation error | Abort before any changes, show error |
| Network timeout | Suggest retrying or checking controller status |
| User cancels | Abort, no changes made |
| Hook blocks operation | Show block message, do not proceed |

### 7.2 Recovery Suggestions

Skills document recovery suggestions for different error types:

| Error Type | Suggestions |
|------------|-------------|
| Authentication | Check credentials, verify API permissions |
| Device not found | Check device name, try MAC or IP, list all clients |
| API error | Check controller status, review error message, retry |
| Partial failure | Use `/infra-undo` to rollback, check UniFi UI |

### 7.3 Audit Trail

All changes are logged to `.claude/logs/` for:
- Troubleshooting failed operations
- Tracking what was changed
- Enabling `/infra-undo` functionality

---

## 8. Natural Language Processing

### 8.1 Intent Recognition

Claude naturally understands infrastructure intents via skill activation:

| User Says | Recognized Intent | Skill/Command |
|-----------|------------------|---------------|
| "Isolate my TV" | Isolate device | `unifi-infra` skill |
| "Create a guest WiFi" | Create guest network | `guest-network` skill |
| "Are there security issues?" | Security audit | `security-audit` skill |
| "Where is my laptop connected?" | Find device | `/infra-find` |
| "Block that suspicious device" | Block device | `/infra-block` |

### 8.2 Parameter Extraction

Claude extracts parameters from natural language:

```
User: "Isolate my Samsung TV to a new VLAN called Media-Devices and let it access my Synology NAS"

Extracted:
- device: "Samsung TV"
- vlan_name: "Media-Devices"
- allow_access_to: ["Synology NAS"]
```

### 8.3 Clarification Flow

When parameters are ambiguous:

```
User: "Isolate the TV"

Claude: I found 2 devices that might be "the TV":
- Living Room TV (Samsung, 192.168.1.45)
- Bedroom TV (LG, 192.168.1.67)

Which one should I isolate?
```

---

## 9. Testing Strategy

Testing is organized into multiple categories in `tests/claude-code/`:

### 9.1 Hook Unit Tests

Automated bash tests for hook scripts:

```bash
# Run all hook tests
./tests/claude-code/hooks/run-hook-tests.sh

# Tests verify:
# - post-change-log.sh creates log entries correctly
# - pre-delete-network.sh blocks protected networks
# - pre-firewall-rule.sh blocks dangerous rules
```

### 9.2 Skill Activation Tests

Manual test scenarios in `tests/claude-code/scenarios/skill-activation.md`:

| Test | Query | Expected |
|------|-------|----------|
| SA-01 | "Isolate my TV" | Skill activates, searches for device |
| SA-02 | "What port is my NAS on?" | Returns switch and port info |
| SA-03 | "Block the guest phone" | Requests confirmation, blocks device |

### 9.3 Command Parsing Tests

Manual test scenarios in `tests/claude-code/scenarios/command-parsing.md`:

| Test | Command | Expected |
|------|---------|----------|
| CP-01 | `/infra-isolate "TV"` | Finds device, creates VLAN plan |
| CP-02 | `/infra-find "192.168.1.50"` | Shows connection details |
| CP-03 | `/infra-undo --list` | Lists recent changes |

### 9.4 Safety Validation Tests

Tests in `tests/claude-code/scenarios/safety-validation.md` verify:
- Protected networks cannot be deleted
- Any-to-any firewall rules are blocked
- Configuration changes require confirmation
- Audit trail captures all changes

### 9.5 Integration Tests

End-to-end workflows in `tests/claude-code/scenarios/integration-flows.md` with mock MCP server.

---

## 10. Project Structure

```
.claude/
├── skills/
│   ├── unifi-infra/
│   │   ├── SKILL.md              # Main infrastructure skill
│   │   ├── PATTERNS.md           # Reusable workflow patterns
│   │   └── SAFETY.md             # Safety rules
│   ├── guest-network/
│   │   └── SKILL.md              # Guest network skill
│   └── security-audit/
│       └── SKILL.md              # Security audit skill
├── commands/
│   ├── infra-isolate.md          # /infra-isolate command
│   ├── infra-find.md             # /infra-find command
│   ├── infra-block.md            # /infra-block command
│   ├── infra-unblock.md          # /infra-unblock command
│   ├── infra-status.md           # /infra-status command
│   ├── infra-undo.md             # /infra-undo command
│   ├── security-audit.md         # /security-audit command
│   ├── infra-guest.md            # /infra-guest command
│   ├── infra-unknown.md          # /infra-unknown command
│   └── infra-rename.md           # /infra-rename command
├── hooks/
│   ├── pre-delete-network.sh     # Block protected network deletion
│   ├── pre-firewall-rule.sh      # Block dangerous firewall rules
│   ├── post-change-log.sh        # Log all configuration changes
│   └── high-risk-notify.sh       # Alert on high-risk operations
├── logs/
│   └── .gitkeep                  # Log directory
└── settings.json                 # Hook configuration

tests/
└── claude-code/
    ├── mocks/                    # Mock MCP server
    ├── hooks/                    # Hook unit tests
    ├── scenarios/                # Test scenarios
    └── fixtures/                 # Test data

docs/
├── user-guide.md                 # End-user documentation
├── command-reference.md          # Command syntax reference
└── developer-guide.md            # Extension documentation
```

---

## 11. Interfaces

### 11.1 Input: From Feature 2 (MCP Server)

This feature depends on Feature 2's MCP tools:
- Query tools for discovering state
- Config tools for making changes
- Rollback data for undo operations

### 11.2 Output: To User

- Confirmation prompts
- Execution results
- Error messages and suggestions
- Notifications via hooks

---

## 12. Open Questions

- [ ] How should skills handle long-running operations?
- [ ] Should there be a "plan only" mode that doesn't execute?
- [ ] How to handle skill versioning as API changes?
- [ ] Should skills be shareable/publishable?

---

## 13. Milestones

| ID | Task | Description |
|----|------|-------------|
| F3.1 | Project Setup | Directory structure, CLAUDE.md, initial settings |
| F3.2 | Core Skills | Main unifi-infra skill with isolation, find, block patterns |
| F3.3 | Slash Commands | All 10 slash commands implemented |
| F3.4 | Hooks Configuration | Safety hooks and audit logging |
| F3.5 | Additional Skills | Guest network and security audit skills |
| F3.6 | Testing Strategy | Hook tests, scenario tests, mock server |
| F3.7 | Documentation | User guide, command reference, developer guide |

---

*Document Version: 1.1*
*Last Updated: 2025-01-10*
