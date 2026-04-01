# Sarvaja Project Rules

> **Sarvaja** (Sanskrit: सर्वज) = "All-Knowing" / Omniscient
> Per DECISION-008: Project renamed from sim.ai (2026-01-14)

## Quick Context
- **Project**: Multi-agent governance platform with TypeDB, LiteLLM, ChromaDB
- **Version**: 1.3.1 | **Updated**: 2026-01-17
- **Repo**: https://github.com/drlegreid/platform-gai

## Document Map

| Need | Document |
|------|----------|
| **Tasks** | [TODO.md](TODO.md) |
| **Gaps** | [docs/gaps/GAP-INDEX.md](docs/gaps/GAP-INDEX.md) |
| **Rules** | [docs/RULES-DIRECTIVES.md](docs/RULES-DIRECTIVES.md) (55 total, 50 in TypeDB) |
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
         ↓                          └── TypeDB :1729 (50 rules)
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

## Shell Commands (CRITICAL)

**NEVER use bare `python` - always use `python3`** - Per WORKFLOW-SHELL-01-v1

| Wrong | Correct |
|-------|---------|
| `python script.py` | `python3 script.py` |
| `python -m pytest` | `python3 -m pytest` |

**Wrapper scripts available:**
- `scripts/python.sh` - Run Python in container
- `scripts/pytest.sh` - Run pytest in container

## Local Development (DEV-VENV-01-v1)

**ALWAYS use project venv. NEVER install to system Python.**

```bash
# Setup (one-time)
sudo apt install -y python3-pip python3-venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Usage
.venv/bin/python script.py
.venv/bin/pytest tests/
```

## Rules Atlas (56 Rules) - Semantic IDs

| Domain | Rules | File |
|--------|-------|------|
| SESSION, REPORT, GOV | Evidence, Decisions, Trust | [RULES-GOVERNANCE.md](docs/rules/RULES-GOVERNANCE.md) |
| ARCH, UI | Architecture, Infrastructure | [RULES-TECHNICAL.md](docs/rules/RULES-TECHNICAL.md) |
| WORKFLOW, TEST, SAFETY, CONTAINER, DOC | Operations | [RULES-OPERATIONAL.md](docs/rules/RULES-OPERATIONAL.md) |

**CRITICAL Rules:** SESSION-EVID-01, TEST-GUARD-01, TEST-E2E-01, CONTAINER-DEV-01, GOV-RULE-01, GOV-BICAM-01, GOV-MCP-FIRST-01, TASK-EPIC-01, WORKFLOW-AUTO-01, WORKFLOW-RD-01, ARCH-INFRA-01, SAFETY-HEALTH-01, TEST-COMP-02, RECOVER-AMNES-01, WORKFLOW-AUTO-02, DOC-LINK-01, TEST-FIX-01, RECOVER-CRASH-01, SAFETY-DESTR-01

## Data Flow Verification (TEST-E2E-01-v1)

**When changing controllers/routes/services, ALL 3 tiers are MANDATORY:**

| Tier | Command | Proves |
|------|---------|--------|
| 1. Unit | `.venv/bin/python3 -m pytest tests/unit/ -q` | Code compiles, interfaces match |
| 2. Integration | `curl http://localhost:8082/api/{endpoint}` | Real API returns correct data |
| 3. Visual CRUD | Playwright CRUD per Gherkin specs | User can create/read/update/delete via UI |

**Tier 3 Gherkin-First Workflow:**
1. Author Gherkin specs → `docs/backlog/specs/E2E-T3-*.gherkin.md`
2. Generate EPIC tasks → `docs/backlog/phases/EPIC-TESTING-E2E.md`
3. Execute via Playwright MCP → click, fill, assert state changes
4. Capture evidence → `evidence/test-results/E2E-T3-*.png`

**Passive screenshots are NOT Tier 3.** CRUD interaction with state change verification is required.

## Test Output Consumption (TEST-HOLO-01-v1)

**NEVER read raw pytest stdout into context.** Use holographic zoom queries instead (97-99% token savings).

**After every test run**, query the holographic store:

| Situation | Zoom | Command | Tokens |
|-----------|------|---------|--------|
| Default / progress check | 1 | `test_evidence_query(zoom=1)` | ~150 |
| Which tests failed? | 2 | `test_evidence_query(zoom=2, status="failed")` | ~500 |
| Reproduce specific failure | 3 | `test_evidence_query(zoom=3, test_id="test_x")` | 2000+ |
| CI badge / one-liner | 0 | `test_evidence_query(zoom=0)` | ~10 |

**Escalation flow:** zoom 1 → 2 → 3 (only escalate on failure investigation).

**Link evidence before closing tasks:**
```python
test_evidence_push(test_id="...", name="...", status="passed", category="unit", task_id="BUG-014")
```

**Pytest flags:** Always add `--compressed-summary` for `[HOLOGRAPHIC-SUMMARY]` output.
**Robot listener:** `--listener tests.evidence.robot_listener.HolographicListener`

## Task Management (GOV-MCP-FIRST-01-v1 — RECOMMENDED)

**MCP gov-tasks re-enabled 2026-03-23 after stability probe (9/9 operations passed).**
**Use MCP for task persistence. TodoWrite for progress display.**

| Action | Use This | Fallback |
|--------|----------|----------|
| Create task | `mcp__gov-tasks__task_create()` | `TodoWrite` |
| Update status | `mcp__gov-tasks__task_update()` | `TodoWrite` |
| Create rule | `mcp__gov-core__rule_create()` | — |
| Start session | `mcp__gov-sessions__session_start()` | — |

**TypeDB** = source of truth for tasks, rules, sessions.

## Session Start Protocol

```
1. health_check()              → Verify TypeDB + ChromaDB
2. backlog_get(limit=10)       → Load prioritized gaps
3. Load to todo list           → Track progress
```

## Provisional Tasks (MCP Fallback)

When MCP unavailable, check [TODO.md](TODO.md) § "Provisional Tasks" for urgent items.

**Current (2026-01-23):**
- GAP-API-500-001: Track Anthropic API 500 error frequency (external)

## Context Recovery Protocol (RECOVER-AMNES-01-v1)

**On compaction/amnesia, ALWAYS check in order:**
```
1. Read CLAUDE.md                   → Document map, architecture
2. Read docs/DEVOPS.md              → Infrastructure setup (CRITICAL)
3. Read .mcp.json                   → Available MCP servers
4. health_check()              → Verify services running
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

- [ ] `health_check()` called at session start
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Gaps tracked in TODO.md
- [ ] No secrets in code (use `.env`)

## Context Efficiency (CONTEXT-SAVE-01-v1)

**Monitor entropy periodically:** `/entropy`

| Tool Calls | Level | Action |
|------------|-------|--------|
| <50 | LOW | Continue |
| 50-100 | MEDIUM | Consider saving |
| 100-150 | HIGH | Save now |
| >150 | CRITICAL | STOP - Save to ChromaDB |

**Before complex tasks:** Check `/entropy` to know your budget.
**After troubleshooting:** Recovery attempts burn context fast.

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
