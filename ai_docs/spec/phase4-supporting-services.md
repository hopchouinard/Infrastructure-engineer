# Phase 4: Supporting Services

Detailed specification for integrating miscellaneous infrastructure services into the homelab engineer.

**Parent Document:** [masteridea.md](./masteridea.md)
**Prerequisites:** Phases 1-3 complete (or can be developed in parallel for some services)
**Status:** Planning - Awaiting Research
**Target Services:** DNS (Pi-hole/AdGuard), Containers (Docker/Portainer), Monitoring (Grafana/Prometheus), Certificates

---

## Features Overview

Phase 4 consists of four features:

| Feature | Name | Spec Document | Description |
|---------|------|---------------|-------------|
| F1 | Documentation & Research | [phase4-f1-documentation-research.md](./phase4-f1-documentation-research.md) | Gathers API docs for all supporting services and establishes project foundation |
| F2 | Infrastructure MCP Server | [phase4-f2-infra-mcp-server.md](./phase4-f2-infra-mcp-server.md) | Exposes supporting service APIs as MCP tools |
| F3 | Claude Code Integration | [phase4-f3-claude-code-integration.md](./phase4-f3-claude-code-integration.md) | Skills, slash commands, hooks |
| F4 | SubAgent Integration | [phase4-f4-subagent-integration.md](./phase4-f4-subagent-integration.md) | Specialized autonomous agents for infrastructure-wide analysis |

**See individual feature specifications for detailed requirements.**

---

## 1. Overview

### 1.1 Goals

Integrate supporting infrastructure services that complement the core systems:
- DNS management (Pi-hole, AdGuard, etc.)
- Container orchestration (Docker, Portainer)
- Monitoring and observability (Grafana, Prometheus, Uptime Kuma)
- Certificate management (Let's Encrypt, local CA)
- Other services as needed

### 1.2 Modular Approach

Unlike Phases 1-3 which each focus on a single system, Phase 4 is a collection of smaller integrations. Services are bundled into a shared `infra-mcp` server with service-specific modules.

```
┌─────────────────────────────────────────────────────────────┐
│                        infra-mcp                             │
│      (unified server with service-specific modules)         │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   dns/       │  docker/     │  monitor/    │   certs/      │
│  (Pi-hole)   │  (Portainer) │  (Grafana)   │ (Lets Encrypt)│
└──────────────┴──────────────┴──────────────┴───────────────┘
```

---

## 2. Prerequisites

### 2.1 Service Inventory

Before implementation, document your supporting services:

```yaml
# To be filled during research phase
services:
  dns:
    platform: ""              # pihole, adguard
    host: ""
    version: ""
    api_available: false

  containers:
    platform: ""              # portainer, docker-direct
    host: ""
    version: ""
    endpoints: []             # Docker endpoints managed

  monitoring:
    grafana:
      host: ""
      version: ""
    prometheus:
      host: ""
      version: ""
    uptime_kuma:
      host: ""
      version: ""

  certificates:
    provider: ""              # letsencrypt, local-ca
    manager: ""               # traefik, nginx-proxy-manager, certbot
    dns_challenge: ""         # cloudflare, etc.

  reverse_proxy:
    platform: ""              # traefik, nginx-proxy-manager
    host: ""
```

### 2.2 Service Checklist

*Check all that apply to your homelab:*

| Service | Category | Priority | Have It? |
|---------|----------|----------|----------|
| Pi-hole | DNS/Ad-blocking | High | [ ] |
| AdGuard Home | DNS/Ad-blocking | High | [ ] |
| Portainer | Container management | High | [ ] |
| Docker (direct) | Container runtime | Medium | [ ] |
| Grafana | Dashboards | Medium | [ ] |
| Prometheus | Metrics | Medium | [ ] |
| InfluxDB | Time-series DB | Low | [ ] |
| Uptime Kuma | Monitoring | Medium | [ ] |
| Traefik | Reverse proxy | Medium | [ ] |
| Nginx Proxy Manager | Reverse proxy | Medium | [ ] |
| cert-manager | Certificates | Low | [ ] |
| Authentik/Authelia | SSO/Auth | Low | [ ] |

### 2.3 API Access Setup

**For each service, document:**
1. API endpoint URL
2. Authentication method (API key, token, username/password)
3. API version and capabilities
4. Rate limits if any

### 2.4 Service Baseline

Document current state before making any changes:

| Item | Current Value | Notes |
|------|---------------|-------|
| DNS records (local) | | Custom DNS entries |
| Container count | | Running containers |
| Monitored endpoints | | Uptime monitors |
| SSL certificates | | Managed certs |

---

## 3. Documentation Corpus

### 3.1 Documentation Sources

#### DNS (Pi-hole / AdGuard)
| Source | URL Pattern | Content Type | Priority |
|--------|-------------|--------------|----------|
| Pi-hole API | `discourse.pi-hole.net/` | HTML | High |
| Pi-hole v6 API | Internal docs | JSON | High |
| AdGuard API | `github.com/AdguardTeam/AdGuardHome/wiki/` | Markdown | High |

#### Containers (Portainer / Docker)
| Source | URL Pattern | Content Type | Priority |
|--------|-------------|--------------|----------|
| Portainer API | `docs.portainer.io/api/` | HTML | High |
| Docker Engine API | `docs.docker.com/engine/api/` | HTML | High |
| Docker SDK Python | `docker-py.readthedocs.io/` | HTML | Medium |

#### Monitoring (Grafana / Prometheus)
| Source | URL Pattern | Content Type | Priority |
|--------|-------------|--------------|----------|
| Grafana HTTP API | `grafana.com/docs/grafana/latest/http_api/` | HTML | High |
| Prometheus API | `prometheus.io/docs/prometheus/latest/querying/api/` | HTML | High |
| Uptime Kuma API | `github.com/louislam/uptime-kuma/wiki/` | Markdown | Medium |

#### Certificates
| Source | URL Pattern | Content Type | Priority |
|--------|-------------|--------------|----------|
| ACME Protocol | RFC 8555 | Text | Medium |
| Traefik Docs | `doc.traefik.io/traefik/` | HTML | High |
| NPM API | Community docs | Various | Medium |

### 3.2 Output Structure

```
ai_docs/vendor/
├── pihole/
│   ├── api/
│   │   ├── endpoints.md
│   │   └── examples/
│   └── local-exports/
├── adguard/
│   ├── api/
│   └── local-exports/
├── portainer/
│   ├── api/
│   └── local-exports/
├── docker/
│   ├── api/
│   └── local-exports/
├── grafana/
│   ├── api/
│   └── local-exports/
├── prometheus/
│   ├── api/
│   └── local-exports/
├── uptime-kuma/
│   ├── api/
│   └── local-exports/
└── certificates/
    ├── acme/
    └── local-exports/
```

---

## 4. MCP Server: `infra-mcp`

### 4.1 Project Structure

See [phase4-f2-infra-mcp-server.md](./phase4-f2-infra-mcp-server.md) for the detailed project structure.

**Key points:**
- Uses **FastMCP pattern** with `@mcp.tool()` decorators for tool registration
- Modular design with service-specific subpackages
- Unified configuration for all services
- Service availability detection (graceful handling of missing services)

```
mcp-servers/infra-mcp/
├── src/infra_mcp/
│   ├── server.py               # MCP server with FastMCP
│   ├── config.py               # Unified configuration
│   ├── services/               # Service-specific modules
│   │   ├── dns/                # Pi-hole / AdGuard
│   │   │   ├── client.py
│   │   │   ├── tools.py
│   │   │   └── models.py
│   │   ├── docker/             # Portainer / Docker
│   │   │   ├── client.py
│   │   │   ├── tools.py
│   │   │   └── models.py
│   │   ├── monitoring/         # Grafana / Prometheus / Uptime Kuma
│   │   │   ├── grafana.py
│   │   │   ├── prometheus.py
│   │   │   ├── uptime_kuma.py
│   │   │   ├── tools.py
│   │   │   └── models.py
│   │   └── certs/              # Certificate management
│   │       ├── client.py
│   │       ├── tools.py
│   │       └── models.py
│   ├── safety/                 # Validation, tiers, rollback
│   └── logging/                # Audit logging
├── tests/
│   └── fixtures/
│       └── api_responses/
├── pyproject.toml
└── README.md
```

### 4.2 Dependencies

```toml
[project]
name = "infra-mcp"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0",              # MCP SDK
    "httpx>=0.27.0",           # Async HTTP client
    "docker>=7.0.0",           # Docker SDK (optional)
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

### 4.3 Configuration

```python
# src/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class InfraConfig(BaseSettings):
    """Configuration loaded from environment."""

    # DNS Service
    dns_platform: str = ""             # "pihole" or "adguard"
    dns_host: str = ""
    dns_api_key: str = ""

    # Container Service
    container_platform: str = ""       # "portainer" or "docker"
    portainer_host: str = ""
    portainer_api_key: str = ""
    docker_host: str = ""              # unix:///var/run/docker.sock

    # Monitoring Services
    grafana_host: str = ""
    grafana_api_key: str = ""
    prometheus_host: str = ""
    uptime_kuma_host: str = ""
    uptime_kuma_api_key: str = ""

    # Certificate Management
    cert_manager: str = ""             # "traefik", "npm", "certbot"
    traefik_host: str = ""
    npm_host: str = ""
    npm_credentials: str = ""

    # Safety settings
    dry_run: bool = False
    require_confirmation: bool = True
    max_changes_per_minute: int = 10

    # Logging
    audit_log_path: str = "ai_docs/logs/infra-changes.log"

    class Config:
        env_file = ".env"
```

---

## 5. Tool Specifications

### 5.1 DNS Management Tools

#### Query Tools (Auto-Approved)
| Tool | Description | Platforms |
|------|-------------|-----------|
| `dns_list_records` | List local DNS records | Pi-hole, AdGuard |
| `dns_get_stats` | Get blocking statistics | Pi-hole, AdGuard |
| `dns_query_log` | Query recent DNS logs | Pi-hole, AdGuard |
| `dns_list_blocklists` | List ad blocklists | Pi-hole, AdGuard |
| `dns_get_status` | Get service status | Pi-hole, AdGuard |

#### Config Tools (Require Confirmation)
| Tool | Description | Risk |
|------|-------------|------|
| `dns_add_record` | Add A/CNAME record | Medium |
| `dns_remove_record` | Remove record | Medium |
| `dns_whitelist` | Whitelist domain | Low |
| `dns_blacklist` | Blacklist domain | Low |
| `dns_add_blocklist` | Add blocklist URL | Medium |
| `dns_remove_blocklist` | Remove blocklist | Medium |
| `dns_enable` | Enable DNS blocking | Low |
| `dns_disable` | Disable DNS blocking | Medium |

### 5.2 Container Management Tools

#### Query Tools (Auto-Approved)
| Tool | Description |
|------|-------------|
| `container_list` | List all containers |
| `container_get` | Get container details |
| `container_logs` | Get container logs |
| `container_stats` | Get container resource usage |
| `stack_list` | List Docker stacks/compose |
| `image_list` | List available images |

#### Config Tools (Require Confirmation)
| Tool | Description | Risk |
|------|-------------|------|
| `container_start` | Start container | Low |
| `container_stop` | Stop container | Low |
| `container_restart` | Restart container | Low |
| `container_create` | Create new container | Medium |
| `container_delete` | Delete container | High |
| `container_exec` | Execute command in container | High |
| `stack_deploy` | Deploy/update stack | High |
| `stack_remove` | Remove stack | High |
| `image_pull` | Pull new image | Medium |
| `image_delete` | Delete image | Medium |

### 5.3 Monitoring Tools

#### Grafana Tools
| Tool | Description | Risk |
|------|-------------|------|
| `grafana_list_dashboards` | List dashboards | Read |
| `grafana_get_dashboard` | Get dashboard JSON | Read |
| `grafana_list_alerts` | List alert rules | Read |
| `grafana_get_alert_status` | Current alert states | Read |
| `grafana_silence_alert` | Create silence | Medium |
| `grafana_query` | Run datasource query | Read |

#### Prometheus Tools
| Tool | Description | Risk |
|------|-------------|------|
| `prometheus_query` | Run instant query | Read |
| `prometheus_query_range` | Run range query | Read |
| `prometheus_list_alerts` | List firing alerts | Read |
| `prometheus_list_targets` | List scrape targets | Read |

#### Uptime Kuma Tools
| Tool | Description | Risk |
|------|-------------|------|
| `uptime_list_monitors` | List all monitors | Read |
| `uptime_get_status` | Get current status | Read |
| `uptime_add_monitor` | Add new monitor | Medium |
| `uptime_remove_monitor` | Remove monitor | Medium |
| `uptime_pause_monitor` | Pause monitoring | Low |
| `uptime_resume_monitor` | Resume monitoring | Low |
| `uptime_get_history` | Get uptime history | Read |

### 5.4 Certificate Management Tools

| Tool | Description | Risk |
|------|-------------|------|
| `cert_list` | List managed certificates | Read |
| `cert_get_status` | Check cert expiry status | Read |
| `cert_request` | Request new certificate | Medium |
| `cert_renew` | Force renewal | Medium |
| `cert_revoke` | Revoke certificate | High |
| `cert_add_domain` | Add domain to cert | Medium |

### 5.5 Complete Tool Summary

| Category | Tools |
|----------|-------|
| **Query (READ)** | `dns_list_records`, `dns_get_stats`, `dns_query_log`, `dns_list_blocklists`, `dns_get_status`, `container_list`, `container_get`, `container_logs`, `container_stats`, `stack_list`, `image_list`, `grafana_list_dashboards`, `grafana_get_dashboard`, `grafana_list_alerts`, `grafana_get_alert_status`, `grafana_query`, `prometheus_query`, `prometheus_query_range`, `prometheus_list_alerts`, `prometheus_list_targets`, `uptime_list_monitors`, `uptime_get_status`, `uptime_get_history`, `cert_list`, `cert_get_status` |
| **Config (LOW)** | `dns_whitelist`, `dns_blacklist`, `dns_enable`, `container_start`, `container_stop`, `container_restart`, `uptime_pause_monitor`, `uptime_resume_monitor` |
| **Config (MEDIUM)** | `dns_add_record`, `dns_remove_record`, `dns_add_blocklist`, `dns_remove_blocklist`, `dns_disable`, `container_create`, `image_pull`, `image_delete`, `grafana_silence_alert`, `uptime_add_monitor`, `uptime_remove_monitor`, `cert_request`, `cert_renew`, `cert_add_domain` |
| **Config (HIGH)** | `container_delete`, `container_exec`, `stack_deploy`, `stack_remove`, `cert_revoke` |

---

## 6. Orchestration Layer

This section provides a high-level overview. See feature specifications for detailed implementations:
- **Feature 3:** [phase4-f3-claude-code-integration.md](./phase4-f3-claude-code-integration.md) - Skills, Commands, Hooks
- **Feature 4:** [phase4-f4-subagent-integration.md](./phase4-f4-subagent-integration.md) - SubAgents for complex analysis

### 6.1 Native Skill System

Skills use **Claude Code's native skill system** - markdown instruction files in `.claude/skills/` that Claude follows when activated.

**Core Skills:**
| Skill | Purpose |
|-------|---------|
| `dns-management` | DNS record and blocklist management |
| `container-ops` | Container lifecycle and stack management |
| `monitoring-ops` | Alert management and metric queries |
| `cert-management` | Certificate lifecycle management |

### 6.2 Slash Commands

Commands in `.claude/commands/` provide explicit, user-invoked workflows:

| Command | Description |
|---------|-------------|
| `/dns-status` | Show DNS service status |
| `/dns-add` | Add DNS record |
| `/dns-block` | Block a domain |
| `/docker-status` | Show container status |
| `/docker-logs` | View container logs |
| `/docker-restart` | Restart container |
| `/deploy-stack` | Deploy Docker stack |
| `/monitor-status` | Show monitoring overview |
| `/cert-status` | Show certificate status |
| `/infra-health` | Full infrastructure health check |

### 6.3 SubAgents (Feature 4)

Specialized autonomous agents for complex analysis tasks:

| Agent | Purpose |
|-------|---------|
| **Infrastructure Health** | Cross-system health and connectivity analysis |
| **DNS Optimizer** | Blocklist optimization and DNS performance |
| **Container Advisor** | Resource optimization and update recommendations |
| **Alert Correlator** | Cross-service alert analysis and root cause |

SubAgents operate read-only and produce **Execution Plans** for user review.

### 6.4 Hooks

Event-driven shell scripts in `.claude/hooks/` for validation and logging:

| Hook | Purpose |
|------|---------|
| `pre-container-delete.sh` | Confirms container deletion |
| `pre-stack-deploy.sh` | Validates stack configuration |
| `post-change-log.sh` | Logs all configuration changes |

---

## 7. Cross-System Integration

### 7.1 Full-Stack Service Deployment

**"Deploy a new web app":**
1. (Proxmox) Create VM or container
2. (UniFi) Ensure VLAN connectivity
3. (Docker) Deploy container stack
4. (DNS) Add DNS record
5. (Certs) Request SSL certificate
6. (Monitoring) Add uptime monitor
7. (Grafana) Create dashboard panel
8. Report: "Service deployed at https://app.homelab.local"

### 7.2 Infrastructure Health Check

**"How's my homelab doing?":**
1. (UniFi) Check gateway, switches, APs status
2. (Proxmox) Check node resources
3. (Docker) Check container health
4. (Monitoring) Check for firing alerts
5. (DNS) Verify DNS resolution
6. (Certs) Check certificate expiry
7. Generate summary report

### 7.3 Incident Response

**"The NAS seems slow":**
1. (UniFi) Check network utilization to NAS
2. (UniFi) Check for packet errors on NAS port
3. (Monitoring) Query NAS metrics (IOPS, latency)
4. (Docker) Check if containers are hammering NAS
5. Suggest remediation based on findings

### 7.4 Cross-System DNS Workflows

| Scenario | Workflow |
|----------|----------|
| New VM created (Proxmox) | Auto-add DNS record for VM hostname |
| New VLAN created (UniFi) | Add DNS entries for VLAN gateway |
| Device blocked (UniFi) | Optionally add to DNS blocklist |
| Service deployed (Docker) | Add DNS record for service |
| New HA device (Home Assistant) | Add DNS record if static IP |

---

## 8. Safety Model

### 8.1 Permission Tiers

| Tier | Operations | Behavior |
|------|-----------|----------|
| **Read** | Query, list, get, logs | Auto-approved |
| **Low** | Start, stop, restart, pause | Brief confirmation |
| **Medium** | Create, add, remove (non-destructive) | Detailed confirmation |
| **High** | Delete, exec, deploy, revoke | Explicit confirmation |
| **Critical** | Stack removal, bulk operations | User-initiated only |

### 8.2 Guardrails

- Never delete running containers without stop first
- Verify stack configuration before deployment
- Prevent deletion of critical DNS records
- Max 10 changes per minute
- All changes logged to audit trail
- Validate certificate domains before request

---

## 9. Testing Strategy

### 9.1 Unit Tests

Mock API responses for all tool tests:

```python
# tests/test_dns_tools.py
import pytest
from respx import MockRouter

@pytest.fixture
def mock_pihole(respx_mock: MockRouter):
    respx_mock.get("/admin/api.php?customdns").respond(json={
        "data": [["192.168.1.100", "nas.local"]]
    })
    return respx_mock

async def test_list_dns_records(mock_pihole, dns_client):
    records = await dns_client.list_records()
    assert len(records) == 1
    assert records[0].hostname == "nas.local"
```

### 9.2 Integration Tests

Run against real services in controlled conditions.

### 9.3 Dry Run Mode

All config tools support `dry_run=True`.

### 9.4 Service Availability

Gracefully handle missing services:

```python
async def list_containers():
    if not config.container_platform:
        return {"error": "Container management not configured"}
    # ... proceed with API call
```

---

## 10. Milestones

Phase 4 milestones are tracked at the feature level. See individual specifications for detailed task breakdowns.

### Feature 1: Documentation & Research
| ID | Milestone |
|----|-----------|
| F1.1 | Project setup |
| F1.2 | DNS service documentation (Pi-hole/AdGuard) |
| F1.3 | Container service documentation (Portainer/Docker) |
| F1.4 | Monitoring service documentation (Grafana/Prometheus/Uptime Kuma) |
| F1.5 | Certificate service documentation |
| F1.6 | Local environment documentation |

### Feature 2: Infrastructure MCP Server
| ID | Milestone |
|----|-----------|
| F2.1 | Project setup and unified configuration |
| F2.2 | DNS module implementation |
| F2.3 | Container module implementation |
| F2.4 | Monitoring module - Grafana |
| F2.5 | Monitoring module - Prometheus |
| F2.6 | Monitoring module - Uptime Kuma |
| F2.7 | Certificate module implementation |
| F2.8 | Safety system |
| F2.9 | Audit logging |
| F2.10 | Service availability detection |
| F2.11 | Testing and documentation |

### Feature 3: Claude Code Integration
| ID | Milestone |
|----|-----------|
| F3.1 | Project setup |
| F3.2 | DNS management skills |
| F3.3 | Container operation skills |
| F3.4 | Monitoring skills |
| F3.5 | Slash commands |
| F3.6 | Hooks configuration |
| F3.7 | Cross-system skills (integration with Phases 1-3) |
| F3.8 | Testing and documentation |

### Feature 4: SubAgent Integration
| ID | Milestone |
|----|-----------|
| F4.1 | Project setup |
| F4.2 | Core agent framework |
| F4.3 | Infrastructure Health agent |
| F4.4 | DNS Optimizer agent |
| F4.5 | Container Advisor agent |
| F4.6 | Alert Correlator agent |
| F4.7 | Agent-to-skill integration |
| F4.8 | Testing and documentation |

See individual feature specifications for complete milestone details.

---

## 11. Open Questions

*To be resolved during research phase:*

- [ ] Which DNS solution do you use (Pi-hole vs AdGuard)?
- [ ] Container management: Portainer or direct Docker?
- [ ] What monitoring stack is in place?
- [ ] SSL certificates: Let's Encrypt, local CA, or manual?
- [ ] Any other services to integrate?
- [ ] Priority order for service implementation?

---

## 12. Research Tasks

*Documentation to gather per service:*

### DNS
- [ ] Pi-hole API documentation (v5 and v6)
- [ ] AdGuard Home API documentation
- [ ] Local DNS record management patterns

### Containers
- [ ] Portainer API documentation
- [ ] Docker SDK capabilities
- [ ] Stack/compose deployment patterns

### Monitoring
- [ ] Grafana HTTP API
- [ ] Prometheus query API
- [ ] Uptime Kuma API (WebSocket-based)

### Certificates
- [ ] ACME protocol overview
- [ ] Traefik cert management API
- [ ] Nginx Proxy Manager API

---

*Document Version: 2.0*
*Last Updated: 2026-01-11*
*Changelog: v2.0 - Restructured to match Phase 1 format with Features Overview (F1-F4), consolidated service modules, added orchestration layer, aligned milestones with feature specs*
