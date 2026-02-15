# Platform Gap Assessment: Session, Project, Tests, Agents & Skills

**Date**: 2026-02-15
**Triggered by**: Building tic-tac-toe + sea-battle Godot projects exposed 7 gap areas
**Status**: ASSESSMENT COMPLETE — Fixes pending

---

## Executive Summary

Building two sample Godot game projects (tic-tac-toe, sea-battle) from within the Sarvaja platform exposed fundamental gaps in session capture, project discovery, test visibility, agent creation, and skill separation. The platform has **complete plumbing** (TypeDB schema, API endpoints, UI tabs) but **incomplete data flow automation** — requiring manual backfill for what should be automatic.

---

## Gap 1: CC Session Data Not in UI

**Symptom**: Sessions created during game development don't appear in the governance dashboard.

**Root Cause**: CC session ingestion is **manual-only**. No auto-discovery on startup, no file watcher.

**Data Flow (Current — Broken)**:
```
CC JSONL files at ~/.claude/projects/-home-oderid-Documents-Vibe-sarvaja-platform/*.jsonl
         ↓
    NO auto-discovery on dashboard load
         ↓
    Must run scripts/ingest_mega_session.py manually
         ↓
    UI shows nothing until ingestion completes
```

**Key Files**:
- `governance/services/cc_session_scanner.py` — Scanner exists but never called automatically
- `governance/services/cc_session_ingestion.py` — Ingestion works but requires explicit invocation
- `governance/services/ingestion_orchestrator.py` — Pipeline orchestration (content + linking phases)
- `scripts/ingest_mega_session.py` — CLI entry point (manual)

**What Exists**: Complete 3-stage pipeline (metadata extraction → ChromaDB content indexing → TypeDB link mining) with checkpoint/resume. Handles 641MB+ files at ~60MB peak memory.

**What's Missing**: Startup scan + background watcher to auto-ingest new CC sessions.

---

## Gap 2: Project Tab Missing Game Projects

**Symptom**: Only PROJ-SARVAJA appears in the project tab. Tic-tac-toe and sea-battle are invisible.

**Three Compounding Problems**:

| Problem | Cause |
|---------|-------|
| No CC project auto-discovery | `cc_session_scanner.py` has `DEFAULT_CC_DIR` but no startup scan |
| Only 1 seed project | `seed/data.py` seeds only `PROJ-SARVAJA` |
| No project creation during ingestion | `ingest_session()` stores `cc_project_slug` but never creates project entity |

**Key Insight**: The game projects were created within the sarvaja-platform CC directory (`~/.claude/projects/-home-oderid-Documents-Vibe-sarvaja-platform/`). CC groups by launch directory, not by target project. There is **no separate CC directory** for the game projects.

**What Exists**: Complete project CRUD (TypeDB schema, REST API, UI tab with headers/detail).

**What's Missing**:
- Auto-discovery from CC directory structure
- Project auto-creation during session ingestion
- Derivation from `cc_project_slug` or CLAUDE.md files in subdirectories

**Key Files**:
- `governance/typedb/queries/projects/crud.py` — TypeDB project operations
- `governance/routes/projects/crud.py` — REST endpoints (GET, POST, DELETE, link)
- `governance/seed/data.py:get_seed_projects()` — Only PROJ-SARVAJA seeded
- `agent/governance_ui/dashboard_data_loader.py:_load_projects()` — UI data loader

---

## Gap 3: Tests Tab Missing Data + No Start/Report Capability

**Symptom**: Tests tab appears empty. Cannot start tests or see detailed reports per category.

**Root Cause**: `dashboard_data_loader.py:load_initial_data()` loads sessions, rules, tasks, agents — but **tests are NOT loaded on startup**. Test data only appears on manual "Refresh" click.

**What Works**:
| Feature | Status |
|---------|--------|
| `POST /tests/run?category=X` — starts tests | Working |
| `POST /tests/cvp/sweep` — runs CVP tiers | Working |
| Results persist to `evidence/test-results/` JSON | Working |
| Heuristic checks (31 total) run via BackgroundTasks | Working |
| Robot Framework integration | Working |

**What's Broken**:
| Feature | Status |
|---------|--------|
| Auto-load test results on dashboard init | Missing |
| Preflight discovery (show "9731 unit tests available") | Missing |
| Category/status/date filtering | Missing |
| Formatted heuristic breakdown (grouped by domain) | Missing — raw JSON only |
| Evidence file navigation from test results | Missing |
| Continuous polling for background test completion | Missing |

**Storage Architecture**: In-memory `_test_results` dict + disk JSON files (no TypeDB). Loads up to 50 persisted files on startup. Lost running state on container restart.

**Key Files**:
- `governance/routes/tests/runner.py` — 8 API endpoints
- `governance/routes/tests/runner_store.py` — In-memory + disk persistence
- `governance/routes/tests/runner_preflight.py` — Test discovery + categories
- `agent/governance_ui/views/tests_view.py` — Tests tab UI layout
- `agent/governance_ui/views/tests_view_panels.py` — Result panels
- `agent/governance_ui/controllers/tests.py` — Controller triggers + polling

---

## Gap 4: Agent Creation + Skill Binding

**Symptom**: Cannot add new agents from the UI. Registration form exists but backend endpoint is missing.

**Critical Bug**: UI registration form at `views/agents/registration.py` **attempts POST to `/api/agents` which doesn't exist**. REST API only has GET, DELETE, PUT (toggle) — no POST create.

**Current Agent Inventory** (5 predefined, all PAUSED):
| Agent ID | Role | Trust | Capabilities |
|----------|------|-------|-------------|
| `code-agent` | Implementation | 0.88 | code_generation, refactoring, test_writing |
| `task-orchestrator` | Delegation | 0.95 | task_management, delegation |
| `rules-curator` | Governance | 0.90 | rule_creation, compliance_review |
| `research-agent` | Research | 0.85 | web_search, document_analysis |
| `local-assistant` | Simple tasks | 0.92 | file_operations, command_execution |

**Skill Binding Mechanism**: Workspace MCP restrictions (soft enforcement via context, not programmatic):
- `workspaces/coding/` — gov-core + gov-tasks MCPs
- `workspaces/curator/` — gov-core + gov-agents + gov-sessions + playwright
- `workspaces/research/` — gov-core + gov-tasks + sequential-thinking
- `workspaces/qa/` — testing tools
- `workspaces/sync/` — background operations

**Agent Type Templates** (in registration form, unusable due to missing POST):
- CODING → rules: [TEST-GUARD-01, TEST-COMP-02, DOC-SIZE-01]
- RESEARCH → rules: [SESSION-EVID-01, GOV-RULE-01]
- CURATOR → rules: [GOV-RULE-01, GOV-BICAM-01, DOC-LINK-01]
- SECURITY → rules: [SAFETY-HEALTH-01, SAFETY-DESTR-01]
- CUSTOM → no default rules

**Additional Missing Pieces**:
- Agent status not persisted to TypeDB (in-memory only — lost on restart)
- `stop_agent_task()` and `end_agent_session()` return placeholder messages
- No task auto-routing/delegation system

**Key Files**:
- `governance/routes/agents/crud.py` — REST endpoints (missing POST)
- `governance/stores/agents.py` — Base config + trust scoring
- `governance/mcp_tools/agents.py` — MCP tools (agent_create exists here)
- `agent/governance_ui/views/agents/registration.py` — UI form (broken)
- `agent/governance_ui/controllers/trust.py` — Controller (register_agent calls missing endpoint)
- `agents.yaml` — Workflow configuration

---

## Gap 5: Game Development Should Be a Separate Skill

**Current Skills** (13 slash commands — all governance-focused):
| Category | Commands |
|----------|----------|
| Session Mgmt | `/health`, `/entropy`, `/session-metrics`, `/context-stats`, `/deep-sleep`, `/spell` |
| Governance | `/checkpoint`, `/report`, `/rule`, `/ingest-check` |
| Task/Bug | `/task`, `/bug`, `/bugfix` |

**Missing**: No commands for game dev, UI prototyping, shader authoring, Godot scaffolding, or creative/external project work.

**No workspaces for**: `workspaces/gamedev/`, `workspaces/creative/`, or any non-governance domain.

---

## Gap 6: Skill Separation Architecture

**Current Architecture**:
```
                    ┌──────────────────────────────────┐
                    │      Claude Code Session          │
                    │   (13 slash commands as skills)    │
                    └──────────┬───────────────────────┘
                               │
           ┌───────────────────┼───────────────────────┐
           ▼                   ▼                        ▼
    ┌──────────┐      ┌──────────────┐         ┌──────────────┐
    │ Platform │      │ Governance   │         │ External     │
    │ Commands │      │ Workspaces   │         │ Projects     │
    │          │      │              │         │              │
    │ /health  │      │ coding/      │         │ Game Dev     │
    │ /entropy │      │ curator/     │         │ Creative     │
    │ /task    │      │ research/    │         │ Other        │
    │ /bug     │      │ qa/          │         │              │
    │ /rule    │      │ sync/        │         │ NOT DEFINED  │
    └──────────┘      └──────────────┘         └──────────────┘
```

**Separation mechanism**: Workspaces + per-workspace CLAUDE.md define tool access and rule focus. Context-based soft enforcement, not programmatic.

**Missing for extensibility**:
- Plugin/extension mechanism for project-specific behaviors
- Dynamic skill registration (skills are hardcoded as `.claude/commands/*.md`)
- Skill-to-agent binding via TypeDB (currently only via workspace CLAUDE.md)

---

## Gap 7: Platform as Generic Solution

**Core Tension**: Sarvaja is built as a governance platform but used for diverse projects (platform dev, game dev, resume building, etc.).

**Generic foundation exists**:
- TypeDB schema supports generic projects, sessions, tasks
- CC session scanner derives project slugs from directory paths
- MCP architecture is modular (6 servers)

**But all implementations are governance-specific**:
- Skills, agents, workspaces — all governance domain
- No plugin mechanism for project-specific behaviors
- No project-type configuration (e.g., "Godot project" vs "Python platform")
- Rules are global, not scoped to project type

---

## Prioritized Fix Plan

| Fix | Impact | Effort | Description |
|-----|--------|--------|-------------|
| **A: Tests Auto-Load** | HIGH | LOW | Add test results loading to `load_initial_data()` |
| **B: Agent Create Endpoint** | HIGH | LOW | Add `POST /api/agents` to match UI registration form |
| **C: Tests on Dashboard Init** | MEDIUM | LOW | Load recent runs + CVP status on startup |
| **D: Project Auto-Discovery** | HIGH | MEDIUM | Scan CC dirs + auto-create projects on startup |
| **E: Game Dev Workspace** | MEDIUM | MEDIUM | Create `workspaces/gamedev/` with Godot skills |
| **F: CC Session Auto-Ingestion** | HIGH | HIGH | Background scan + auto-ingest new CC sessions |
| **G: Agent Status Persistence** | MEDIUM | MEDIUM | Persist agent status to TypeDB schema |
| **H: Test Results Formatting** | MEDIUM | MEDIUM | Group heuristic results by domain, add filters |

### Recommended Implementation Order

```
Phase 1 (Quick Wins — 1 session):
  Fix A: Tests auto-load on dashboard init
  Fix B: POST /api/agents endpoint

Phase 2 (Core Data Flow — 1-2 sessions):
  Fix C: Test results + CVP status in load_initial_data()
  Fix D: Project auto-discovery from CC directories

Phase 3 (Architecture — 2-3 sessions):
  Fix E: Game dev workspace + skill definition
  Fix F: CC session auto-ingestion (background watcher)

Phase 4 (Polish — 1-2 sessions):
  Fix G: Agent status TypeDB persistence
  Fix H: Test results formatting + filters
```

---

## Evidence

- CC project directories: `~/.claude/projects/` (4 directories found)
- Game projects built: `/home/oderid/Documents/Vibe/godot-games/tic-tac-toe/` (commit `de201e5`) and `sea-battle/` (commit `b9dd305`)
- Test suite: 9731 unit tests (batches 1-172)
- Agent count: 5 predefined, all PAUSED
- Slash commands: 13 (all governance-domain)
- Workspaces: 5 (coding, curator, research, qa, sync)
