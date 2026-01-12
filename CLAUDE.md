# Sim.ai PoC Project Rules

## Quick Context
- **Project**: Multi-agent platform with TypeDB Governance, LiteLLM, ChromaDB
- **Version**: 1.1.0 | **Updated**: 2026-01-11
- **Repo**: https://github.com/drlegreid/platform-gai

## Document Map

| Need | Document |
|------|----------|
| **Tasks** | [TODO.md](TODO.md) |
| **Gaps** | [docs/gaps/GAP-INDEX.md](docs/gaps/GAP-INDEX.md) |
| **Rules** | [docs/RULES-DIRECTIVES.md](docs/RULES-DIRECTIVES.md) (42 total) |
| **DevOps** | [docs/DEVOPS.md](docs/DEVOPS.md) |
| **Shell Guide** | [docs/SHELL-GUIDE.md](docs/SHELL-GUIDE.md) |
| **MCP Config** | [.claude/MCP.md](.claude/MCP.md) |
| **Hooks** | [.claude/HOOKS.md](.claude/HOOKS.md) |
| **Workflows** | [.windsurf/workflows.md](.windsurf/workflows.md) |

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

> Per DECISION-003 (TypeDB-First) | Per RULE-036 (MCP Split)

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| UI | Trame + Vuetify | Python-first |
| Rules | TypeDB (1729) | Inference engine |
| Search | ChromaDB (8001) | Vector embeddings |
| LLM | LiteLLM (4000) | Multi-provider |
| Agents | Agno | TypeDB integration |

## Rules Atlas (42 Rules)

| Category | Rules | File |
|----------|-------|------|
| Governance | 001, 003, 006, 011, 013, 018, 019, 026, 029, 034 | [RULES-GOVERNANCE.md](docs/rules/RULES-GOVERNANCE.md) |
| Technical | 002, 007-010, 016, 017, 035, 036, 040 | [RULES-TECHNICAL.md](docs/rules/RULES-TECHNICAL.md) |
| Operational | 004, 005, 012, 014, 015, 020-033, 037, 041, 042 | [RULES-OPERATIONAL.md](docs/rules/RULES-OPERATIONAL.md) |

**CRITICAL Rules (16):** 001 (evidence), 008 (rewrite), 009 (versions), 010 (wisdom), 011 (governance), 014 (halt), 015 (R&D), 016 (infra), 021 (health), 023 (test), 024 (AMNESIA), 031 (continue), 034 (links), 037 (fix-validation), 041 (crash), 042 (no-destructive)

## Session Start Protocol

```
1. governance_health()              → Verify TypeDB + ChromaDB
2. governance_get_backlog(limit=10) → Load prioritized gaps
3. Load to todo list                → Track progress
```

## Context Recovery Protocol (RULE-024)

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

**Claude-Mem Fallback (when TypeDB/ChromaDB down):**
```
mcp__claude-mem__chroma_query_documents(["sim-ai 2026-01 infrastructure"])
```

**Key ports:** Dashboard=8081, API=8082, TypeDB=1729, ChromaDB=8001

**Never ask user "what were we doing?" - recover context autonomously.**

## Crash Prevention (RULE-041)

**File Size Limits (CRITICAL):**
- Max tokens per file read: **25,000 tokens** (~500-750 lines)
- Before reading large files: `wc -l <file>` to check line count
- Use `offset/limit` parameters or `Grep` for large files
- Exception: JSON/log files often exceed limits - always use Grep

**Save Context Before Risk:**
```python
# Before complex operations, save session context
chroma_save_session_context(
    session_id="SESSION-YYYY-MM-DD-TOPIC",
    summary="What was accomplished",
    key_decisions=["decision1", "decision2"],
    files_modified=["file1.py", "file2.py"],
    gaps_discovered=["GAP-XXX"]
)
```

**On Crash (exit code 1):**
```bash
# Check logs first
grep -i "error\|crash" ~/.config/Code/logs/*/window1/exthost/Anthropic.claude-code/*.log | tail -20
```

## Development Philosophy

- **Incremental progress** - Small changes that compile and pass tests
- **Files ≤300 lines** - Per RULE-032, modularize larger files
- **PARTIAL = Subtasks** - Per RULE-033, break down large tasks
- **Max 3 attempts** - Then document, research alternatives, try different angle

## Quick Checks

- [ ] `governance_health()` called at session start
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Gaps tracked in TODO.md
- [ ] No secrets in code (use `.env`)

## Halt Commands (RULE-014)

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
