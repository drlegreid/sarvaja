# Sim.ai PoC Project Rules

## Quick Context
- **Project**: Multi-agent platform with TypeDB Governance, LiteLLM, ChromaDB
- **Version**: 1.0.0
- **Location**: `C:\Users\natik\Documents\Vibe\sim-ai\sim-ai`
- **Repo**: https://github.com/drlegreid/platform-gai
- **Updated**: 2024-12-25

## 🗺️ Document Map (LLM Entry Point)

| Need | Document | Lines |
|------|----------|-------|
| **Tasks** | [`TODO.md`](TODO.md) | ~100 |
| **Gaps** | [`docs/gaps/GAP-INDEX.md`](docs/gaps/GAP-INDEX.md) | ~60 |
| **R&D** | [`docs/backlog/R&D-BACKLOG.md`](docs/backlog/R&D-BACKLOG.md) | ~100 |
| **Rules (Index)** | [`docs/RULES-DIRECTIVES.md`](docs/RULES-DIRECTIVES.md) | ~120 |
| **Rules (Details)** | [`docs/rules/`](docs/rules/) | 3 files |
| **Workflows** | [`.windsurf/workflows.md`](.windsurf/workflows.md) | ~260 |
| **Deployment** | [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | ~130 |

### Cross-Reference Index
```
RULE-001,003,006,011,013 → docs/rules/RULES-GOVERNANCE.md
RULE-002,007,008,009,010 → docs/rules/RULES-TECHNICAL.md
RULE-004,005,012,014     → docs/rules/RULES-OPERATIONAL.md
GAP-*                    → docs/gaps/GAP-INDEX.md
R&D-*                    → docs/backlog/R&D-BACKLOG.md
DECISION                 → evidence/SESSION-DECISIONS-*.md
Completed Tasks          → docs/tasks/TASKS-COMPLETED.md
```

## Architecture (v1.0 - DECISION-001, DECISION-003)
```
┌─────────────────────────────────────────────────────────────┐
│                 Sim.ai v1.0 Stack (5 containers)            │
├─────────────────────────────────────────────────────────────┤
│  Agents (7777)  │  LiteLLM (4000)  │  Ollama (11434)       │
├─────────────────────────────────────────────────────────────┤
│  ChromaDB (8001)        │  TypeDB (1729)                    │
│  └── Semantic search    │  └── Governance inference         │
│  └── 53 docs            │  └── 25 rules, 8 decisions        │
└─────────────────────────────────────────────────────────────┘
```
> Opik removed per DECISION-001 | TypeDB-First per DECISION-003

## Technology Decisions (GAP-CTX-001)

> **CRITICAL:** Agents MUST be aware of these decisions during refactoring

| Decision | Choice | NOT Using | Rationale |
|----------|--------|-----------|-----------|
| **UI Framework** | Trame + Vuetify | React, raw Vue.js | Python-first, Vuetify components |
| **Rule Engine** | TypeDB (1729) | SQL, MongoDB | TypeQL inference, graph relations |
| **Semantic Search** | ChromaDB (8001) | Elasticsearch | Vector embeddings, MCP integration |
| **LLM Routing** | LiteLLM (4000) | Direct API calls | Multi-provider abstraction |
| **Agent Framework** | Agno | LangChain, CrewAI | Lightweight, TypeDB integration |
| **Observability** | Removed Opik | Kept Opik | DECISION-001: Memory overhead |

**UI Stack Details:**
- **Trame**: Python server-side rendering with Vue.js frontend
- **Vuetify**: Material Design components (v-data-table, v-card, etc.)
- **State Management**: `agent/governance_ui/state/` modules
- **Views**: `agent/governance_ui/views/` (12 modules)
- **Controllers**: `agent/governance_ui/controllers/` (10 modules)

**When Refactoring UI:**
1. Use Trame's `state` for reactivity, NOT Vue refs
2. Use Vuetify components, NOT raw HTML
3. Follow existing view patterns in `governance_ui/views/`
4. Register controllers via `register_all_controllers()`

## Rules Atlas (25 Total - Context-Optimized)

> **Navigation**: Use TypeDB MCP or markdown fallback. Full details in linked files.

| Category | Rules | File |
|----------|-------|------|
| **Governance** | RULE-001, 003, 006, 011, 013 | [`RULES-GOVERNANCE.md`](docs/rules/RULES-GOVERNANCE.md) |
| **Technical** | RULE-002, 007, 008, 009, 010 | [`RULES-TECHNICAL.md`](docs/rules/RULES-TECHNICAL.md) |
| **Operational** | RULE-004, 005, 012, 014, 021-033 | [`RULES-OPERATIONAL.md`](docs/rules/RULES-OPERATIONAL.md) |

**CRITICAL Rules (Always Active):**
- `RULE-001`: Session evidence logging
- `RULE-011`: Multi-agent trust governance
- `RULE-014`: Autonomous halt commands (STOP, HALT, STAI, RED ALERT)
- `RULE-021`: MCP healthcheck at session start
- `RULE-024`: AMNESIA recovery protocol

> **Index**: [`docs/RULES-DIRECTIVES.md`](docs/RULES-DIRECTIVES.md) | **TypeDB**: `governance_query_rules()`

### Rule Access Hierarchy (RULE-021 Integration)

```
┌─────────────────────────────────────────────────────────────────┐
│                    RULE ACCESS HIERARCHY                         │
├─────────────────────────────────────────────────────────────────┤
│  1. SESSION START: Call governance_health MCP tool               │
│     └── If healthy → Use TypeDB MCP governance (25 rules)        │
│     └── If unhealthy → Fallback to markdown files                │
│                                                                   │
│  2. PRIMARY: MCP Governance TypeDB (Port 1729)                   │
│     └── governance_query_rules, governance_get_rule              │
│     └── Inference engine, dependency chains                      │
│                                                                   │
│  3. FALLBACK: Markdown Rule Files (when TypeDB unavailable)      │
│     └── docs/rules/RULES-GOVERNANCE.md (RULE-001,003,006,011,013)│
│     └── docs/rules/RULES-TECHNICAL.md (RULE-002,007,008,009,010) │
│     └── docs/rules/RULES-OPERATIONAL.md (RULE-004,005,012,014+)  │
│     └── docs/RULES-DIRECTIVES.md (index)                         │
└─────────────────────────────────────────────────────────────────┘
```

**Per RULE-021 Level 2:** At session start, ALWAYS call `governance_health` first.
If `action_required: START_SERVICES` → notify user with recovery command.

### Backlog Sync Protocol (TASK 1.3)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SESSION START PROTOCOL                        │
├─────────────────────────────────────────────────────────────────┤
│  1. Call governance_health → Verify services up                  │
│  2. Call governance_get_backlog(limit=20) → Get prioritized gaps │
│  3. Load gaps into Claude todo list → Track actual backlog       │
│                                                                   │
│  CRITICAL: Never create self-referential todo lists!             │
│  GAP-INDEX.md is the source of truth (182 gaps, 138 open)        │
└─────────────────────────────────────────────────────────────────┘
```

**MCP Tools for Backlog:**
- `governance_get_backlog(limit)` - Get prioritized open gaps
- `governance_gap_summary()` - Get gap statistics
- `governance_get_critical_gaps()` - Get all CRITICAL gaps

### Quick Checks
- [ ] Session log created in `./docs/`
- [ ] No secrets in code (use `.env`)
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Gaps tracked in `./TODO.md`

## Development Philosophy

### Core Beliefs
- **Incremental progress** - Small changes that compile and pass tests
- **Learn from existing code** - Study patterns before implementing
- **Clear intent over clever code** - Choose boring, obvious solutions
- **Files ≤300 lines** - Per RULE-032, modularize larger files ([details](docs/rules/RULES-OPERATIONAL.md#rule-032))
- **PARTIAL = Subtasks** - Per RULE-033, break down large tasks ([details](docs/rules/RULES-OPERATIONAL.md#rule-033))

### When Stuck (Max 3 Attempts)
After 3 failed attempts on an issue, **STOP** and:
1. Document what failed and specific errors
2. Research 2-3 alternative approaches
3. Question if this is the right abstraction level
4. Try a fundamentally different angle

### Definition of Done
- [ ] Tests written and passing
- [ ] Code follows project conventions
- [ ] No linter warnings
- [ ] Commit messages explain "why"
- [ ] No TODOs without issue numbers

### Never Do
- Use `--no-verify` to bypass hooks
- Disable tests instead of fixing them
- Commit code that doesn't compile
- Silently swallow exceptions

## Testing (Per RULE-023)

### Running Tests (PowerShell)
```powershell
# Run all tests (from project root)
Set-Location "c:\Users\natik\Documents\Vibe\sim-ai\sim-ai"
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_mcp_evidence.py -v

# Run with short traceback
python -m pytest tests/ -v --tb=line

# Run fast tests only (skip integration)
python -m pytest tests/ -v -m "not integration"

# Show last 40 lines of output
$result = python -m pytest tests/test_mcp_evidence.py -v --tb=line 2>&1
$result | Select-Object -Last 40
```

### Key Test Files
| File | Tests | Purpose |
|------|-------|---------|
| `tests/test_mcp_evidence.py` | 27 | Evidence MCP tools (sessions, decisions, tasks) |
| `tests/test_mcp_tasks.py` | 14 | Tasks CRUD MCP tools (TypeDB) |
| `tests/test_mcp_agents.py` | 9 | Agents CRUD MCP tools (TypeDB) |
| `tests/test_governance_ui.py` | 36 | Governance Dashboard UI |
| `tests/test_mcp_config.py` | 10 | MCP server configuration |

### TDD Pattern (RED-GREEN-REFACTOR)
1. **Write test first** in `tests/test_*.py`
2. **Run test** - should FAIL (RED)
3. **Implement** in `governance/mcp_tools/*.py`
4. **Run test** - should PASS (GREEN)
5. **Add backward compat export** if needed in `governance/mcp_server.py`

## DevOps Commands (RULE-031)

### CORE MCP Dependencies
```
CORE_SERVICES = ["docker", "typedb", "chromadb"]
- Docker Desktop must be running
- TypeDB (port 1729) - Rule inference engine
- ChromaDB (port 8001) - Semantic search for claude-mem
```

### Command Hierarchy (Use in Order)
```
1. WRAPPER (deploy.ps1) - Full stack with validation
   .\deploy.ps1 -Action up -Profile cpu

2. DIRECT (docker compose) - Reliable, no PowerShell quirks
   docker compose --profile cpu up -d typedb chromadb

3. INDIVIDUAL - Surgical container control
   docker start sim-ai-typedb-1
   docker stop sim-ai-chromadb-1
```

> **Note**: deploy.ps1 has strict `$ErrorActionPreference='Stop'` which can fail on docker info warnings. Use direct docker compose for auto-recovery.

### Running Services (via deploy.ps1)
```powershell
# Start stack
.\deploy.ps1 -Action up -Profile cpu

# Check status
.\deploy.ps1 -Action status

# View logs
.\deploy.ps1 -Action logs

# Health check
.\deploy.ps1 -Action health

# Run tests
.\deploy.ps1 -Action test

# Pull Ollama models
.\deploy.ps1 -Action pull-models

# Start Opik dashboard
.\deploy.ps1 -Action opik

# Rebuild containers
.\deploy.ps1 -Action rebuild

# Stop stack
.\deploy.ps1 -Action down
```

### Direct Docker Commands (Reliable Fallback)
```powershell
# Start CORE services only
docker compose --profile cpu up -d typedb chromadb

# Start all services
docker compose --profile cpu up -d

# Check running containers
docker ps --format "table {{.Names}}\t{{.Status}}"

# View container logs
docker logs sim-ai-typedb-1 --tail 50

# Restart specific container
docker restart sim-ai-typedb-1

# Stop all
docker compose --profile cpu down
```

## Key Files
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Stack orchestration |
| `config/litellm_config.yaml` | Model routing |
| `agents.yaml` | Agent definitions |
| `agent/playground.py` | Agent server code |
| `agent/sync_agent.py` | Sync agent skeleton |
| `.env.example` | Environment template |

## Claude Code Configuration Paths

```
┌─────────────────────────────────────────────────────────────────┐
│                 CLAUDE CODE CONFIG LOCATIONS                     │
├─────────────────────────────────────────────────────────────────┤
│  GLOBAL (User-level):                                            │
│  ├── C:\Users\natik\.claude.json       ← MCP servers config     │
│  ├── C:\Users\natik\.claude\settings.json  ← Hooks & settings   │
│  └── %APPDATA%\Claude\logs\            ← Desktop app logs       │
│                                                                   │
│  PROJECT (Repository-level):                                     │
│  ├── .mcp.json                         ← Project MCP servers    │
│  ├── .claude\settings.local.json       ← Project hooks          │
│  └── CLAUDE.md                         ← Project instructions   │
└─────────────────────────────────────────────────────────────────┘
```

### CORE MCP Servers (6 Total - Stability-Tested)
| Server | Purpose | Risk |
|--------|---------|------|
| `claude-mem` | Memory via ChromaDB | LOW |
| `governance` | TypeDB rules (project .mcp.json) | LOW |
| `llm-sandbox` | Python code execution | LOW |
| `sequential-thinking` | Reasoning chains | LOW |
| `git` | Git operations | LOW |
| `powershell` | Windows shell commands | LOW |

### UTILITY MCPs (Disabled 2026-01-01 - See R&D TOOL-009)
| Server | Reason Disabled | Backup Location | Re-enable When |
|--------|-----------------|-----------------|----------------|
| `desktop-commander` | Memory overhead | `.claude/mcp-backup.json` | Need file/process ops |
| `playwright` | Browser automation heavy | `.claude/mcp-backup.json` | Need web testing |
| `filesystem` | Redundant with Bash/Read tools | `.claude/mcp-backup.json` | Never |
| `godot-mcp` | Game dev specific | `.claude/mcp-backup.json` | Godot project work |

### High-Risk MCPs (Removed - Never Enable)
| Server | Issue | Removed Date |
|--------|-------|--------------|
| `context7` | NPX cold start, external API | 2024-12-14 |
| `octocode` | Rate limits, external API crashes | 2026-01-01 |

### Hook Event Nesting Rules
```
WITHOUT matchers (SessionStart, Stop, SessionEnd):
  [{ "type": "command", "command": "...", "timeout": N }]

WITH matchers (PostToolUse, UserPromptSubmit, PreToolUse):
  [{ "matcher": "*", "hooks": [{ "type": "command", "command": "...", "timeout": N }] }]
```

## Health Checks
```powershell
# LiteLLM
Invoke-WebRequest -Uri "http://localhost:4000/health" -Headers @{Authorization="Bearer sk-litellm-master-key-change-me"}

# ChromaDB
Invoke-WebRequest -Uri "http://localhost:8001/api/v2/heartbeat"

# Ollama
Invoke-WebRequest -Uri "http://localhost:11434/api/tags"

# Agents
Invoke-WebRequest -Uri "http://localhost:7777/health"
```

## Session Directives
- **Evidence Trail**: Document decisions and rationale in session logs
- **Gap Tracking**: Add discovered gaps to TODO.md immediately
- **Test Coverage**: Update tests when fixing issues
- **Sync to GitHub**: Push significant changes to drlegreid/platform-gai
- **Context Preservation** (GAP-WORKFLOW-001): Run `/save` before:
  - Major task transitions
  - Approaching context limit
  - Before autonomous execution concludes
  - When user indicates session ending

## Autonomous Execution (RULE-030)
When instructed to "continue" or work "autonomously":
1. **DO NOT STOP** until all backlog items are resolved or context limit reached
2. **Prioritize** by: CRITICAL > HIGH > MEDIUM > LOW
3. **Per RULE-012**: Files >300 lines MUST be modularized
4. **Per RULE-014**: Only halt on explicit commands (STOP, HALT, STAI, RED ALERT)
5. **Track progress** in TODO.md and GAP-INDEX.md after each completion
6. **Run tests** after each modularization to verify no regressions
7. **Chain tasks**: After completing one gap, immediately start the next highest priority

## Quick Commands
```powershell
# Full deployment sequence
.\deploy.ps1 -Action up
.\deploy.ps1 -Action pull-models
.\deploy.ps1 -Action health
.\deploy.ps1 -Action test

# Start monitoring
.\deploy.ps1 -Action opik

# Push to GitHub (excludes credentials)
git add -A; git commit -m "message"; git push origin master
```

## Windsurf Workflows

See `.windsurf/workflows.md` for:
- Session start protocol
- Gap discovery & documentation
- Session evidence export
- DevOps operations
- Integration testing
- Memory interaction protocol

---

## 📚 Related Projects (Cross-Links)

| Project | Purpose | Location |
|---------|---------|----------|
| **angelgai** | Crash recovery, MCP stability | `../../../angelgai` |
| **localgai** | claude-mem, EBMSF methodology | `../../../localgai` |
| **godot-mcp** | Game dev MCP | `../../../godot-mcp` |

> **Migration guide:** [`docs/MIGRATION-FROM-LEGACY.md`](docs/MIGRATION-FROM-LEGACY.md)

---
*Keep this file <100 lines. Details in linked docs.*
