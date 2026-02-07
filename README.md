# Sarvaja Platform

> **Sarvaja** (Sanskrit: सर्वज) = "All-Knowing" / Omniscient

Multi-agent governance platform with TypeDB, LiteLLM, and ChromaDB. Provides AI-assisted task management, rule-based governance, and session tracking.

**Version**: 1.3.1 | **Updated**: 2026-02-08

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLAUDE CODE HOST                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    MCP SERVERS                               │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │   │
│  │  │ gov-core   │ │ gov-agents │ │gov-sessions│ │ gov-tasks │ │   │
│  │  │ (Rules)    │ │ (Trust)    │ │ (DSM)      │ │ (Gaps)    │ │   │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬─────┘ │   │
│  │        └──────────────┴──────────────┴──────────────┘       │   │
│  │                           │                                  │   │
│  │                    TypeDB + ChromaDB                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────────┐
│                     PODMAN STACK (5 containers)                      │
│                                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐       │
│  │ Dashboard  │ │  LiteLLM   │ │   Ollama   │ │  ChromaDB  │       │
│  │   :8081    │ │   :4000    │ │  :11434    │ │   :8001    │       │
│  │  REST API  │ │ (Router)   │ │  (Local)   │ │ (Vectors)  │       │
│  │   :8082    │ │            │ │            │ │            │       │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘       │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                      TypeDB :1729                            │    │
│  │              (Rules, Sessions, Tasks, Agents)                │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env → Set ANTHROPIC_API_KEY

# 2. Create Python virtual environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Start Podman stack
podman compose --profile cpu --profile dashboard-dev up -d

# 4. Verify services
podman compose --profile cpu ps

# 5. Access dashboard
open http://localhost:8081
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| **Dashboard** | 8081 | Trame/Vue 3 governance UI |
| **REST API** | 8082 | FastAPI backend |
| **TypeDB** | 1729 | Graph database (rules, sessions, tasks) |
| **ChromaDB** | 8001 | Vector embeddings (claude-mem) |
| **LiteLLM** | 4000 | Model routing proxy |
| **Ollama** | 11434 | Local CPU inference |

## MCP Servers

The platform exposes governance functionality via Model Context Protocol (MCP):

| Server | Purpose | Key Tools |
|--------|---------|-----------|
| `gov-core` | Rules management | `rules_query`, `rule_create`, `rule_update` |
| `gov-agents` | Agent trust | `agents_list`, `agent_trust_update` |
| `gov-sessions` | Session tracking | `session_start`, `session_decision` |
| `gov-tasks` | Task management | `task_create`, `task_verify`, `backlog_get` |

## Key Features

### Governance Dashboard
- **Rules View**: Browse 55+ governance rules with filtering and search
- **Sessions View**: Track agent sessions with evidence and tool calls
- **Tasks View**: Manage task backlog with phase/status filters
- **Infrastructure View**: Monitor service health and MCP status

### Document Linkage
Rules and tasks can link to source documents (markdown files in `docs/rules/`). Click "Source Document" in detail views to open the file viewer.

### CRUD Operations
Full create, read, update, delete support for:
- Rules (`/api/rules`)
- Tasks (`/api/tasks`)
- Sessions (`/api/sessions`)
- Decisions (`/api/decisions`)

## Development

```bash
# Run tests
.venv/bin/pytest tests/ -v

# Run dashboard locally (outside container)
.venv/bin/python -m agent.governance_dashboard

# Check API health
curl http://localhost:8082/api/health
```

## Container Commands

**IMPORTANT: Use Podman, not Docker** (per xubuntu migration)

```bash
# Start services
podman compose --profile cpu --profile dashboard-dev up -d

# Stop services
podman compose --profile cpu down

# View logs
podman logs <container_id>

# Restart dashboard
podman compose --profile dev restart governance-dashboard-dev

# Rebuild dashboard image
podman build -t platform_governance-dashboard-dev:latest -f Dockerfile.dashboard .
```

## Project Structure

```
platform/
├── agent/                  # Dashboard and UI components
│   ├── governance_dashboard.py
│   └── governance_ui/      # Trame/Vue 3 views and controllers
├── governance/             # Backend services
│   ├── routes/             # FastAPI endpoints
│   ├── services/           # Business logic
│   └── stores/             # Data access (TypeDB, in-memory)
├── docs/
│   ├── rules/              # Rule source documents (leaf/*.md)
│   ├── gaps/               # Gap tracking (GAP-INDEX.md)
│   └── DEVOPS.md           # Infrastructure guide
├── tests/
│   ├── unit/               # Python unit tests
│   ├── robot/              # Robot Framework E2E tests
│   └── e2e/                # End-to-end integration tests
└── evidence/               # Session evidence files
```

## Documentation

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | Project rules and session protocols |
| [docs/DEVOPS.md](docs/DEVOPS.md) | Infrastructure and deployment |
| [docs/gaps/GAP-INDEX.md](docs/gaps/GAP-INDEX.md) | Open gaps and improvements |
| [docs/RULES-DIRECTIVES.md](docs/RULES-DIRECTIVES.md) | All 55 governance rules |
| [.claude/MCP.md](.claude/MCP.md) | MCP server configuration |

## Current Status (2026-02-08)

- [x] TypeDB integration with 55 governance rules
- [x] Governance dashboard with Trame/Vue 3
- [x] MCP servers for all domains (core, agents, sessions, tasks)
- [x] REST API with full CRUD operations
- [x] Document viewer for rule source files
- [x] Session evidence attachment and viewing
- [x] Heuristic data integrity checks
- [x] Robot Framework E2E test suite

## Troubleshooting

**TypeDB not connecting:**
```bash
# Check if TypeDB container is running
podman ps | grep typedb

# Restart TypeDB
podman compose --profile cpu restart typedb
```

**Dashboard shows stale data:**
- Click "Refresh" button in the UI
- Or restart the dashboard container

**MCP server errors:**
```bash
# Check for orphan containers
podman ps -a | grep mcp

# Remove orphans
podman rm -f <container_name>
```

## License

Private - All rights reserved.
