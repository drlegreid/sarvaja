# Sarvaja Project Rules

> **Sarvaja** (Sanskrit: सर्वज) = "All-Knowing" / Omniscient
> Per DECISION-008: Project renamed from sim.ai (2026-01-14)

## Quick Context
- **Project**: Multi-agent governance platform with TypeDB, LiteLLM, ChromaDB
- **Version**: 1.3.0 | **Updated**: 2026-01-14
- **Repo**: https://github.com/drlegreid/platform-gai

## Document Map

| Need | Document |
|------|----------|
| **Tasks** | [TODO.md](TODO.md) |
| **Gaps** | [docs/gaps/GAP-INDEX.md](docs/gaps/GAP-INDEX.md) |
| **Rules** | [docs/RULES-DIRECTIVES.md](docs/RULES-DIRECTIVES.md) (41 total) |
| **DevOps** | [docs/DEVOPS.md](docs/DEVOPS.md) |
| **Shell Guide** | [docs/SHELL-GUIDE.md](docs/SHELL-GUIDE.md) |
| **MCP Config** | [.claude/MCP.md](.claude/MCP.md) |
| **Hooks** | [.claude/HOOKS.md](.claude/HOOKS.md) |
| **Taxonomy** | [docs/rules/leaf/META-TAXON-01-v1.md](docs/rules/leaf/META-TAXON-01-v1.md) |

## Architecture

```
Claude Code Host                    Podman Stack (5 containers)
├── governance-core (Rules)         ├── Dashboard :8081
├── governance-agents (Trust)       ├── LiteLLM :4000
├── governance-sessions (DSM)       ├── Ollama :11434
└── governance-tasks (Gaps)         ├── ChromaDB :8001
         ↓                          └── TypeDB :1729 (41 rules)
    MCP → TypeDB + ChromaDB
```

## Container Runtime (CRITICAL)

**USE PODMAN, NOT DOCKER** - xubuntu migration 2026-01-09

| Command | Use Instead |
|---------|-------------|
| `docker` | `podman` |
| `docker-compose` | `podman compose` |
| `docker ps` | `podman compose --profile cpu ps` |

Data persistence: `/home/oderid/Documents/Docker/` (bind mounts)

> Per DECISION-003 (TypeDB-First) | Per ARCH-MCP-02-v1 (MCP Split)

## Rules Atlas (41 Rules) - Semantic IDs

| Domain | Rules | File |
|--------|-------|------|
| SESSION, REPORT, GOV | Evidence, Decisions, Trust | [RULES-GOVERNANCE.md](docs/rules/RULES-GOVERNANCE.md) |
| ARCH, UI | Architecture, Infrastructure | [RULES-TECHNICAL.md](docs/rules/RULES-TECHNICAL.md) |
| WORKFLOW, TEST, SAFETY, CONTAINER, DOC | Operations | [RULES-OPERATIONAL.md](docs/rules/RULES-OPERATIONAL.md) |

**CRITICAL Rules:** SESSION-EVID-01, TEST-GUARD-01, CONTAINER-DEV-01, GOV-RULE-01, GOV-BICAM-01, WORKFLOW-AUTO-01, WORKFLOW-RD-01, ARCH-INFRA-01, SAFETY-HEALTH-01, TEST-COMP-02, RECOVER-AMNES-01, WORKFLOW-AUTO-02, DOC-LINK-01, TEST-FIX-01, RECOVER-CRASH-01, SAFETY-DESTR-01

## Session Start Protocol

```
1. governance_health()              → Verify TypeDB + ChromaDB
2. governance_get_backlog(limit=10) → Load prioritized gaps
3. Load to todo list                → Track progress
```

## Context Recovery Protocol (RECOVER-AMNES-01-v1)

**On compaction/amnesia, ALWAYS check in order:**
```
1. Read CLAUDE.md                   → Document map, architecture
2. Read docs/DEVOPS.md              → Infrastructure setup (CRITICAL)
3. Read .mcp.json                   → Available MCP servers
4. governance_health()              → Verify services running
5. Read TODO.md                     → Current tasks
6. Read docs/gaps/GAP-INDEX.md      → Open gaps
```

**BEFORE any destructive action (reset, wipe, delete):**
```
1. podman compose --profile cpu ps  → Check actual running containers
2. Query claude-mem                 → Recent migration/infrastructure changes
3. Read docs/DEVOPS.md              → Correct commands for environment
```

**Key ports:** Dashboard=8081, API=8082, TypeDB=1729, ChromaDB=8001

**Never ask user "what were we doing?" - recover context autonomously.**

## Crash Prevention (RECOVER-CRASH-01-v1)

**File Size Limits (CRITICAL):**
- Max tokens per file read: **25,000 tokens** (~500-750 lines)
- Before reading large files: `wc -l <file>` to check line count
- Use `offset/limit` parameters or `Grep` for large files

**Save Context Before Risk:**
```python
chroma_save_session_context(
    session_id="SESSION-YYYY-MM-DD-TOPIC",
    summary="What was accomplished",
    key_decisions=["decision1"],
    files_modified=["file1.py"],
    gaps_discovered=["GAP-XXX"]
)
```

## Development Philosophy

- **Incremental progress** - Small changes that compile and pass tests
- **Files ≤300 lines** - Per DOC-SIZE-01-v1, modularize larger files
- **PARTIAL = Subtasks** - Per DOC-PARTIAL-01-v1, break down large tasks
- **Max 3 attempts** - Then document, research alternatives

## Quick Checks

- [ ] `governance_health()` called at session start
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Gaps tracked in TODO.md
- [ ] No secrets in code (use `.env`)

## Halt Commands (WORKFLOW-AUTO-01-v1)

| Command | Action |
|---------|--------|
| `STOP`, `HALT`, `STAI` | Immediate halt, save state |
| `RED ALERT` | Emergency stop |

## Related Projects

| Project | Purpose |
|---------|---------|
| [angelgai](../../../angelgai) | Crash recovery, MCP stability |
| [localgai](../../../localgai) | claude-mem, EBMSF methodology |

---
*Target: <100 lines. Details in linked docs.*
