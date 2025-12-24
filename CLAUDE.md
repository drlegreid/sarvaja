# Sim.ai PoC Project Rules

## Quick Context
- **Project**: Multi-agent platform with LiteLLM, ChromaDB, Opik
- **Location**: `C:\Users\natik\Documents\Vibe\sim-ai\sim-ai`
- **Repo**: https://github.com/drlegreid/platform-gai
- **Updated**: 2024-12-24

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

## Architecture (Simplified - DECISION-001)
```
┌─────────────────────────────────────────────────────────────┐
│                 Sim.ai PoC Stack (4 containers)             │
├─────────────────────────────────────────────────────────────┤
│  Agents (7777)  │  LiteLLM (4000)  │  Ollama (11434)       │
├─────────────────────────────────────────────────────────────┤
│  ChromaDB (8001) - 53 docs from claude-mem                  │
└─────────────────────────────────────────────────────────────┘
```
> Opik removed per DECISION-001 (overkill for current needs)

## Core Rules (14 Active)

| Rule | Directive | Priority |
|------|-----------|----------|
| **RULE-001** | Session Evidence Logging | CRITICAL |
| **RULE-007** | MCP Usage Protocol | HIGH |
| **RULE-011** | Multi-Agent Governance | CRITICAL |
| **RULE-012** | Deep Sleep Protocol (DSP) | HIGH |
| **RULE-014** | Autonomous Task Sequencing | CRITICAL |

> **Full rules:** [`docs/RULES-DIRECTIVES.md`](docs/RULES-DIRECTIVES.md)
> **Halt commands (RULE-014):** STOP, HALT, STAI, RED ALERT, ALERT

### Quick Checks
- [ ] Session log created in `./docs/`
- [ ] No secrets in code (use `.env`)
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Gaps tracked in `./TODO.md`

## Running Services (via deploy.ps1)
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

## Key Files
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Stack orchestration |
| `config/litellm_config.yaml` | Model routing |
| `agents.yaml` | Agent definitions |
| `agent/playground.py` | Agent server code |
| `agent/sync_agent.py` | Sync agent skeleton |
| `.env.example` | Environment template |

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
