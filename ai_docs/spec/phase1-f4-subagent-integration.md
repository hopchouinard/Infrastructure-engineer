# Phase 1 - Feature 4: SubAgent Integration

Specialized autonomous agents for complex infrastructure analysis, troubleshooting, design consultation, and change planning.

**Parent Document:** [phase1-unifi.md](./phase1-unifi.md)
**Dependencies:**
- Feature 2 (UniFi MCP Server) - provides the underlying tools
- Feature 3 (Claude Code Integration) - provides skills and commands that agents invoke
**Status:** Planning

---

## 1. Purpose

### 1.1 What This Feature Does

While Feature 3 provides Skills (auto-activated workflows) and Commands (user-triggered workflows), Feature 4 introduces **SubAgents**—specialized autonomous agents that handle complex, multi-step analysis tasks:

- **Infrastructure Design Advisor**: Consultative agent for network architecture decisions
- **Network Troubleshooter**: Diagnostic agent for complex connectivity issues
- **Security Deep Audit**: Thorough security analysis beyond quick audits
- **Change Planner**: Simulation and planning for complex multi-resource changes

### 1.2 Why SubAgents Matter

Skills and Commands are excellent for **executing known workflows**. SubAgents excel at **exploratory, reasoning-heavy tasks** where:

- The path isn't predetermined (requires investigation)
- Multiple data sources must be correlated
- Deep domain expertise is needed
- Background processing is beneficial
- Complex plans need to be formulated before execution

### 1.3 SubAgent vs Skill Decision Matrix

| Characteristic | Use Skill/Command | Use SubAgent |
|----------------|-------------------|--------------|
| **Execution pattern** | Known steps | Exploratory |
| **Duration** | Fast (seconds) | Variable (may be minutes) |
| **Reasoning depth** | Low-Medium | High |
| **User interaction** | Immediate results | May run in background |
| **Output** | Actions executed | Analysis + recommendations |
| **Configuration changes** | Can execute directly | Produces execution plan only |

### 1.4 Scope

| In Scope | Out of Scope |
|----------|--------------|
| 4 specialized SubAgents | Custom SubAgent builder |
| Read-only investigation via Skills | Direct configuration changes |
| Execution plan generation | Automatic plan execution |
| Integration with F3 infrastructure | Cross-system agents (Phase 2+) |
| Background execution support | Real-time monitoring agents |

---

## 2. Architecture

### 2.1 SubAgent Position in Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User                                     │
│                          │                                       │
│    "Design a camera      │     "Why is my TV                    │
│     network setup"       │      disconnecting?"                 │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                Feature 4: SubAgents                              │
├──────────────────────────┼───────────────────────────────────────┤
│                          ▼                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              SubAgent Dispatcher                            │ │
│  │   Selects appropriate agent based on task type             │ │
│  └────────────┬──────────┬──────────┬──────────┬─────────────┘ │
│               │          │          │          │               │
│  ┌────────────▼──┐  ┌────▼────┐  ┌──▼───┐  ┌──▼──────────┐    │
│  │ Design        │  │ Trouble-│  │ Sec. │  │ Change      │    │
│  │ Advisor       │  │ shooter │  │ Audit│  │ Planner     │    │
│  └───────┬───────┘  └────┬────┘  └──┬───┘  └──┬──────────┘    │
│          │               │          │          │               │
│          └───────────────┴──────────┴──────────┘               │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │           Read-Only Skill/Command Invocation              │  │
│  │  • Can call: /infra-find, /infra-status, query tools      │  │
│  │  • Cannot call: /infra-isolate, /infra-block, config tools│  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │              Execution Plan Generator                     │  │
│  │  For any recommended changes, produces:                   │  │
│  │  • Step-by-step plan                                      │  │
│  │  • Commands/skills to run                                 │  │
│  │  • Risk assessment                                        │  │
│  │  • Rollback strategy                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│         Feature 3: Skills & Commands                              │
│         (User executes recommended plan manually)                 │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **SubAgent Dispatcher** | Routes tasks to appropriate agent based on context |
| **Individual Agents** | Domain-specific expertise and reasoning |
| **Read-Only Gateway** | Ensures agents only invoke non-destructive operations |
| **Execution Plan Generator** | Formats recommendations into actionable plans |

### 2.3 Permission Model

SubAgents operate under a **strict read-only constraint**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SubAgent Permissions                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ ALLOWED (Read/Investigate)                                   │
│  ─────────────────────────────                                   │
│  • Query MCP tools (unifi_list_*, unifi_get_*, unifi_search_*)  │
│  • Read-only Skills and Commands (/infra-find, /infra-status)   │
│  • Read files (ai_docs/, logs, configs)                         │
│  • Analyze and correlate data                                   │
│  • Produce reports and recommendations                          │
│  • Generate execution plans                                      │
│                                                                  │
│  ❌ PROHIBITED (Modify/Execute)                                  │
│  ─────────────────────────────                                   │
│  • Config MCP tools (unifi_create_*, unifi_delete_*, etc.)      │
│  • Modifying Skills (/infra-isolate, /infra-block, etc.)        │
│  • Writing files (except designated output locations)           │
│  • Direct execution of recommended changes                       │
│                                                                  │
│  📋 OUTPUT FORMAT                                                │
│  ─────────────────────────────                                   │
│  • Analysis results and findings                                │
│  • Recommendations with rationale                               │
│  • Execution Plan (for user to review and execute)              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. SubAgent Catalog

### 3.1 Infrastructure Design Advisor

**Purpose:** Consultative agent for network architecture decisions, capacity planning, and infrastructure improvements.

**Activation triggers:**
- "How should I set up..."
- "What's the best way to design..."
- "I want to add [devices], how should I structure..."
- "Review my network architecture"
- "Plan expansion for..."

**Capabilities:**
- Analyze current network topology
- Recommend VLAN segmentation strategies
- Suggest firewall rule architectures
- Plan for capacity and growth
- Compare design alternatives with trade-offs
- Reference best practices from vendor documentation

**Example interaction:**
```
User: "I want to add 4 security cameras and an NVR. How should I set this up?"

[Design Advisor investigates]:
- Queries current VLANs, subnets, firewall rules
- Checks available VLAN IDs
- Reviews existing IoT/camera patterns
- Considers bandwidth and storage requirements

[Design Advisor recommends]:
- Dedicated "Cameras" VLAN (e.g., VLAN 35)
- Subnet sizing for camera count + growth
- Firewall rules: Cameras→NVR only, block internet
- Switch port assignments
- PoE budget considerations

[Produces Execution Plan]:
1. /infra-isolate with specific parameters
2. Firewall rule commands
3. Port configuration steps
```

### 3.2 Network Troubleshooter

**Purpose:** Diagnostic agent for complex connectivity and performance issues.

**Activation triggers:**
- "Why is [device] disconnecting?"
- "Troubleshoot [connectivity issue]"
- "Debug network problem with..."
- "[Device] can't reach [destination]"
- "Slow network performance on..."

**Capabilities:**
- Correlate client status, AP health, switch ports
- Analyze historical patterns (if logs available)
- Check for IP conflicts, DHCP issues
- Review firewall rules blocking traffic
- Identify WiFi interference patterns
- Trace traffic paths through network

**Example interaction:**
```
User: "My TV keeps losing WiFi connection"

[Troubleshooter investigates]:
- Gets TV client details (signal, AP, roaming history)
- Checks AP status and client count
- Reviews channel congestion
- Checks for IP/DHCP issues
- Looks for patterns in disconnect timing

[Troubleshooter diagnoses]:
- TV connected to far AP (-72 dBm signal)
- Closer AP exists but TV not roaming
- Channel overlap with neighbor's network
- Possible cause: Poor roaming + interference

[Produces Recommendations]:
- Consider wired connection (TV location near switch)
- Or: Adjust AP power levels to improve roaming
- Or: Change WiFi channel to avoid interference
```

### 3.3 Security Deep Audit

**Purpose:** Comprehensive security analysis beyond the quick `/infra-audit` command.

**Activation triggers:**
- "Deep security audit"
- "Comprehensive security review"
- "Check my network security thoroughly"
- "Pen test my network configuration"
- "Security hardening recommendations"

**Capabilities:**
- All `/infra-audit` checks, plus:
- Cross-reference against security frameworks (CIS, NIST)
- Analyze attack surface per VLAN
- Review authentication configurations
- Check for common misconfigurations
- Identify unnecessary services/exposure
- Historical trend analysis

**Difference from `/infra-audit`:**

| Aspect | /infra-audit (Command) | Security Deep Audit (SubAgent) |
|--------|------------------------|--------------------------------|
| Duration | Seconds | Minutes |
| Depth | Surface checks | Comprehensive analysis |
| Output | Quick report | Detailed findings + remediation |
| Background | No | Can run in background |
| Framework alignment | No | References security standards |

### 3.4 Change Planner

**Purpose:** Plan and simulate complex multi-resource infrastructure changes.

**Activation triggers:**
- "Plan migration of..."
- "I want to reorganize my VLANs"
- "Help me restructure..."
- "What's the safest way to change..."
- "Simulate impact of..."

**Capabilities:**
- Inventory affected resources
- Determine dependency order
- Identify potential disruptions
- Calculate rollback strategies
- Estimate downtime per change
- Produce phased execution plan

**Example interaction:**
```
User: "I want to reorganize all my IoT devices into proper categories"

[Change Planner investigates]:
- Lists all IoT-type devices
- Current VLAN assignments
- Firewall rules affecting them
- Device dependencies (e.g., hub devices)

[Change Planner produces]:
Phase 1: Create new VLANs (Cameras, Sensors, Smart Home)
Phase 2: Migrate cameras first (lowest risk)
Phase 3: Migrate sensors
Phase 4: Migrate smart home devices (most dependencies)
Phase 5: Clean up old rules

[Execution Plan]:
- Specific commands for each phase
- Expected downtime per device category
- Rollback commands if issues arise
- Verification steps between phases
```

---

## 4. Execution Plan Format

All SubAgents that recommend changes must produce a standardized **Execution Plan**:

```markdown
## Execution Plan: [Title]

*Generated by: [Agent Name]*
*Generated at: [Timestamp]*

---

### Summary

[1-3 sentence summary of what this plan accomplishes]

### Prerequisites

- [ ] [Any prerequisites that must be true before starting]
- [ ] [e.g., "Backup current config", "Maintenance window scheduled"]

### Execution Steps

#### Phase 1: [Phase Name]

**Risk Level:** [Low/Medium/High]
**Estimated Duration:** [Time estimate]
**Affected Resources:** [List]

| Step | Command/Action | Purpose |
|------|----------------|---------|
| 1.1 | `/infra-isolate "Device" --vlan-name "Name"` | Create isolated VLAN |
| 1.2 | [Next command] | [Purpose] |

**Verification:**
```
/infra-find "Device"  # Should show new VLAN
```

**Rollback (if needed):**
```
/infra-undo --id [step_1.1_rollback]
```

#### Phase 2: [Next Phase]
...

### Post-Execution Verification

- [ ] [Verification step 1]
- [ ] [Verification step 2]

### Rollback Strategy

If major issues occur:
1. [Step-by-step rollback instructions]
2. [Commands to run]

---

**Ready to execute?** Review the plan above, then run each phase's commands manually.
For questions about any step, ask before executing.
```

---

## 5. Agent Definition Format

Each SubAgent is defined as a markdown file in `.claude/agents/`:

```yaml
# .claude/agents/[agent-name]/AGENT.md
---
name: agent-identifier
description: |
  Multi-line description of what this agent does.
  Used for automatic activation based on user intent.
  Include trigger phrases and use cases.
tools: Read, Grep, Glob
model: sonnet
---

# [Agent Name]

[Detailed instructions for the agent's behavior, reasoning patterns,
investigation workflows, and output formats]
```

**Supported Frontmatter Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent identifier (lowercase-hyphens) |
| `description` | Yes | When to invoke; supports multi-line with `\|` |
| `tools` | No | Comma-separated allowlist of tools |
| `disallowedTools` | No | Comma-separated denylist of tools |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit` |

**Note:** Non-standard configuration (allowed/prohibited commands, context files, output format) should be documented in the agent's system prompt body, not in frontmatter. These are behavioral instructions for the agent.

---

## 6. Integration Points

### 6.1 With Feature 3 (Skills/Commands)

SubAgents can invoke read-only Skills and Commands:

| Can Invoke | Cannot Invoke |
|------------|---------------|
| `/infra-find` | `/infra-isolate` |
| `/infra-status` | `/infra-block` |
| `/infra-unknown` | `/infra-unblock` |
| `/security-audit` (quick mode, without `--deep`) | `/infra-guest` |
| | `/infra-rename` |
| | `/infra-undo` |

### 6.2 With Feature 2 (MCP Server)

SubAgents can call query MCP tools directly:

| Can Call | Cannot Call |
|----------|-------------|
| `unifi_list_networks` | `unifi_create_network` |
| `unifi_get_client` | `unifi_delete_network` |
| `unifi_list_firewall_rules` | `unifi_create_firewall_rule` |
| `unifi_get_port_status` | `unifi_set_port_vlan` |
| `unifi_search_clients` | `unifi_block_client` |

### 6.3 With Documentation (ai_docs/)

SubAgents have read access to:
- `ai_docs/vendor/unifi/` - Vendor documentation for best practices
- `ai_docs/spec/` - Project specifications for context
- `ai_docs/logs/` - Historical change logs for pattern analysis

---

## 7. User Experience

### 7.1 Invoking SubAgents

SubAgents can be invoked:

1. **Automatically** (context-based activation):
   ```
   User: "How should I set up network segmentation for my smart home devices?"
   [Design Advisor activates automatically]
   ```

2. **Explicitly** (via slash command):
   ```
   User: /design "camera network setup"
   User: /troubleshoot "TV connectivity"
   User: /security-audit --deep
   User: /plan "VLAN reorganization"
   ```

3. **Background execution**:
   ```
   User: /security-audit --deep --background
   [Agent runs in background, user continues working]
   [Notification when complete]
   ```

### 7.2 Interacting During Investigation

SubAgents may ask clarifying questions:

```
[Design Advisor]: I found 12 IoT devices. Before I recommend a segmentation
strategy, I'd like to understand:

1. Do you want cameras on a separate VLAN from other IoT devices?
2. Do any IoT devices need to communicate with each other?
3. Is there a specific security concern driving this redesign?
```

### 7.3 Reviewing Execution Plans

After investigation, SubAgents present execution plans:

```
[Change Planner]: Based on my analysis, here's the execution plan for
reorganizing your IoT devices:

## Execution Plan: IoT Segmentation Restructure
...

Would you like me to:
1. Explain any step in more detail?
2. Modify the plan (e.g., different VLAN IDs)?
3. [You execute the plan manually when ready]
```

---

## 8. Testing Strategy

### 8.1 Agent Behavior Tests

- Verify agents activate on appropriate triggers
- Confirm read-only constraint is enforced
- Test execution plan format compliance
- Validate clarifying question flow

### 8.2 Integration Tests

- SubAgent → Skill/Command invocation
- SubAgent → MCP tool queries
- SubAgent → Documentation access
- Background execution and notification

### 8.3 Permission Tests

- Verify agents cannot call config tools
- Verify agents cannot invoke modifying commands
- Test rejection of plan auto-execution attempts

---

## 9. Project Structure

```
.claude/
├── agents/
│   ├── shared/                            # Shared patterns (F4.1, F4.2, F4.7)
│   │   ├── PERMISSION-MODEL.md            # Read-only constraints (F4.1)
│   │   ├── EXECUTION-PLAN-TEMPLATE.md     # Standard plan format (F4.1)
│   │   ├── QUERY-PATTERNS.md              # Common investigation patterns (F4.1)
│   │   ├── AGENT-BASE-PATTERN.md          # Standard agent structure (F4.2)
│   │   ├── INVESTIGATION-WORKFLOWS.md     # Investigation patterns (F4.2)
│   │   ├── ANALYSIS-FRAMEWORKS.md         # Analysis methodologies (F4.2)
│   │   ├── OUTPUT-FORMATS.md              # Report/plan formats (F4.2)
│   │   ├── ERROR-HANDLING.md              # Error recovery patterns (F4.2)
│   │   ├── SUCCESS-METRICS.md             # Quality targets (F4.2)
│   │   ├── CROSS-AGENT-PATTERNS.md        # Handoff patterns (F4.2)
│   │   ├── USER-INTERACTION.md            # Interaction guidelines (F4.2)
│   │   ├── SKILL-INTEGRATION.md           # Skill/command invocation (F4.7)
│   │   └── INTEGRATION-TESTS.md           # Integration test scenarios (F4.7)
│   ├── tests/                             # Test documentation (F4.8)
│   │   ├── TEST-SCENARIOS.md              # Detailed test scenarios
│   │   ├── TEST-CHECKLIST.md              # Quick verification checklist
│   │   └── TEST-RESULTS-TEMPLATE.md       # Results recording template
│   ├── design-advisor/                    # Design Advisor agent (F4.3)
│   │   ├── AGENT.md                       # Agent definition
│   │   ├── PATTERNS.md                    # Design patterns reference
│   │   └── TEMPLATES.md                   # Output templates
│   ├── troubleshooter/                    # Troubleshooter agent (F4.4)
│   │   ├── AGENT.md
│   │   ├── DIAGNOSTICS.md                 # Diagnostic procedures
│   │   └── COMMON-ISSUES.md               # Known issue patterns
│   ├── security-audit/                    # Security Audit agent (F4.5)
│   │   ├── AGENT.md
│   │   ├── CHECKLISTS.md                  # Security checklists
│   │   └── FRAMEWORKS.md                  # CIS/NIST references
│   └── change-planner/                    # Change Planner agent (F4.6)
│       ├── AGENT.md
│       ├── SIMULATION.md                  # Impact simulation patterns
│       └── ROLLBACK.md                    # Rollback strategy templates
├── commands/
│   ├── design.md                          # /design command (F4.1)
│   ├── troubleshoot.md                    # /troubleshoot command (F4.1)
│   └── plan.md                            # /plan command (F4.1)
│   # Note: /security-audit is defined in F3.3; --deep flag invokes F4.5 SubAgent
└── settings.json                          # No F4-specific changes needed
```

**Note:** Agents are automatically discovered from the `.claude/agents/` directory structure. The settings.json file does not require F4-specific updates for agent registration.

---

## 10. Milestones

| ID | Milestone | Description |
|----|-----------|-------------|
| F4.1 | Project Setup | Directory structure, base configuration |
| F4.2 | Core Agent Framework | Shared patterns, permission model, execution plan format |
| F4.3 | Design Advisor | Infrastructure consultation agent |
| F4.4 | Troubleshooter | Network diagnostics agent |
| F4.5 | Security Audit | Deep security analysis agent |
| F4.6 | Change Planner | Multi-resource change planning agent |
| F4.7 | Agent-to-Skill Integration | Read-only skill/command invocation |
| F4.8 | Testing Strategy | Comprehensive agent testing |
| F4.9 | Documentation | User guide and agent reference |

---

## 11. Open Questions

- [ ] Should agents be able to save analysis results to files for future reference?
- [ ] How should agent "memory" work across sessions (remember previous analyses)?
- [ ] Should there be a "meta-agent" that coordinates multiple agents for complex tasks?
- [ ] How to handle agent disagreement (e.g., Design Advisor and Security Audit conflict)?

---

## 12. Future Enhancements (Post-Phase 1)

- **Cross-system agents**: Agents that span UniFi + Proxmox + Home Assistant
- **Custom agent builder**: Users define their own specialized agents
- **Agent collaboration**: Multiple agents working together on complex problems
- **Learning from feedback**: Agents improve recommendations based on outcomes

---

*Document Version: 1.1*
*Last Updated: 2026-01-10*
*Changelog: v1.1 - Corrected agent definition format to match Claude Code frontmatter spec, updated project structure to include shared/ and tests/ directories, fixed integration points command names*
