# Sarvaja Platform

> **Sarvaja** (Sanskrit: सर्वज) = "All-Knowing" / Omniscient

A governance platform that makes AI-assisted development visible, traceable, and intelligent. Sarvaja automatically discovers your Claude Code sessions, links them to rules, tasks, and decisions in a TypeDB graph, and surfaces everything through a 15-view dashboard — so every conversation, tool call, and design choice becomes a first-class governance entity.

**Version**: 1.0-GA | **Updated**: 2026-03-20 | [Release Notes](docs/releases/V1.0-GA.md) | [Changelog](CHANGELOG.md)

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

## Flagship Feature: Sessions Management for Claude Code

Sarvaja v1's headline capability — full lifecycle tracking of Claude Code development sessions.

- **Auto-Discovery**: Scans `~/.claude/projects/` on startup, ingests all JSONL session files
- **Streaming Ingestion**: Handles 600MB+ files with ~60MB peak memory
- **Transcript Viewing**: Color-coded conversation cards with 4-tier fallback
- **Zoom-Level Detail**: Progressive disclosure from summary to full thinking content
- **Entity Linking**: Sessions ↔ rules, decisions, tasks, evidence in TypeDB
- **Validation**: CVP heuristic checks for data integrity

See the full [Sessions Management Guide](docs/features/SESSIONS-MANAGEMENT.md).

## Key Features

### Governance Dashboard (15 Views)
- **Chat**: Natural language interaction with `/status`, `/tasks`, `/sessions` commands
- **Rules**: Browse 48+ governance rules with CRUD, filtering, and document linkage
- **Agents**: Trust scores, status toggle (PAUSED/ACTIVE), linked sessions
- **Tasks**: Full backlog with phase/status filters, create dialog, pagination
- **Sessions**: Session tracking with evidence, tool calls, and agent linking
- **Decisions**: Strategic decision log with rule linking
- **Executive**: Period-based reports and analytics
- **Impact**: Rule dependency analysis with Mermaid diagrams
- **Trust**: Agent trust leaderboard and governance proposals
- **Workflow**: Compliance checks and LangGraph DSP workflow
- **Audit**: Full audit trail with entity/action/actor filters
- **Monitor**: Real-time event feed with alerts
- **Infrastructure**: Service health, MCP status, container logs
- **Metrics**: Session analytics and tool usage statistics
- **Tests**: Heuristic data integrity checks (27 checks across 6 domains)

### Data Integrity (Heuristic Checks)
27 automated checks across TASK, SESSION, RULE, AGENT, CROSS-ENTITY, and EXPLORATORY domains. Run via `/api/tests/heuristic/run` or the Tests tab.

### Audit Trail
All CRUD operations generate audit entries with correlation IDs, actor attribution, and rule application tracking. Persisted to `data/audit_trail.json` with 7-day retention.

### CRUD Operations
Full create, read, update, delete support for:
- Rules (`/api/rules`)
- Tasks (`/api/tasks`)
- Sessions (`/api/sessions`)
- Decisions (`/api/decisions`)
- Agents (`/api/agents`)

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
│   ├── unit/               # 10,500+ Python unit tests
│   ├── robot/              # Robot Framework E2E tests
│   └── e2e/                # End-to-end integration tests
├── evidence/               # Session evidence files
└── data/                   # Persistent data (audit trail, agent metrics)
```

## Documentation

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | Project rules and session protocols |
| [docs/DEVOPS.md](docs/DEVOPS.md) | Infrastructure and deployment |
| [docs/gaps/GAP-INDEX.md](docs/gaps/GAP-INDEX.md) | Open gaps and improvements |
| [docs/RULES-DIRECTIVES.md](docs/RULES-DIRECTIVES.md) | All 56 governance rules |
| [docs/features/SESSIONS-MANAGEMENT.md](docs/features/SESSIONS-MANAGEMENT.md) | Sessions feature deep dive |
| [docs/releases/V1.0-GA.md](docs/releases/V1.0-GA.md) | v1 release notes |
| [.claude/MCP.md](.claude/MCP.md) | MCP server configuration |

## Test Suite

```bash
# Unit tests (10,500+ tests)
.venv/bin/python3 -m pytest tests/unit/ -q

# Heuristic integrity checks (27 checks)
curl -X POST http://localhost:8082/api/tests/heuristic/run

# E2E tests
.venv/bin/python3 -m pytest tests/e2e/ -v
```

## Current Status (v1.0-GA, 2026-03-20)

- [x] **Sessions Management** — CC auto-discovery, JSONL ingestion, transcripts, entity linking
- [x] TypeDB integration with 56 governance rules (50 in TypeDB)
- [x] Governance dashboard with 15 views (Trame/Vue 3)
- [x] 4 MCP servers with 100+ tools (core, agents, sessions, tasks)
- [x] REST API with full CRUD + audit trail
- [x] Streaming ingestion pipeline for 600MB+ session files
- [x] 27 heuristic data integrity checks (6 domains)
- [x] 10,500+ unit tests passing (98% governance coverage)
- [x] Orchestrator workflow with dynamic ROI-based budget
- [x] Agent trust scoring, governance proposals, and voting
- [x] Chat with natural language + command interface
- [x] Workspaces & capabilities management

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

## Limitations
1. for research purposes only
2. for sequential use of the API
3. only for personal use

## Roadmap
0. implement event 'sourced governor > worker' workflow which should be always sequential
1. cleanup project
2. stabilize rules mcp engine
3. improve test tab - to support GUI test results visualision & authoring
4. implement guardrails which will enforce limitations
5. test how it works with local LLM againts a sandbox project

## License

[Apache 2.0 License](LICENSE)

