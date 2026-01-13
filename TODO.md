# TODO Index - Sim.ai PoC

**Updated:** 2026-01-12 | **Backlog System:** [GAP-INDEX.md](docs/gaps/GAP-INDEX.md)

---

## Task System

| Source | Access | Purpose |
|--------|--------|---------|
| **GAP-INDEX.md** | [docs/gaps/GAP-INDEX.md](docs/gaps/GAP-INDEX.md) | Gap tracking (189 total) |
| **Governance MCP** | `governance_get_backlog()` | Prioritized open gaps |
| **R&D Backlog** | [R&D-BACKLOG.md](docs/backlog/R&D-BACKLOG.md) | Strategic R&D items |
| **Completed** | [TASKS-COMPLETED.md](docs/tasks/TASKS-COMPLETED.md) | Archive |

---

## Session Start Protocol

```
1. governance_health()              → Verify services
2. governance_get_backlog(limit=10) → Load prioritized gaps
3. Load to Claude Code todo list    → Track progress
```

---

## Current Stats (2026-01-13)

| Metric | Count |
|--------|-------|
| Total Gaps | 202 |
| RESOLVED | 175 |
| OPEN | 27 |
| DEFERRED | ~15 |
| Rules | 47 (all synced to TypeDB) |

---

## ULTRA HIGH Priority (Intent-Based Workflow)

> **Purpose:** Group tasks by strategic intent to enforce completion workflow
> **Workflow:** implement → validate (static) → test (exploratory) → evidence → commit
> **Rule:** Per REPORT-SUMM-01-v1: All work must produce summary with evidence

| ID | Task | Status | Intent |
|----|------|--------|--------|
| ULTRA-001 | Data Integrity Tests (bottom-up) | TODO | Validate foundation |
| ULTRA-002 | Certification Issue + Evidence | DONE | Milestone closure |
| ULTRA-003 | Push all changes to GitHub | DONE | Ship it |

---

## Priority Gaps (OPEN)

> Use `governance_get_critical_gaps()` for latest list

| Priority | Count | Focus Areas |
|----------|-------|-------------|
| **CRITICAL** | 0 | All resolved! |
| **HIGH** | 0 | All resolved! |
| **MEDIUM** | 7 | Deferred/R&D |
| **LOW** | 20 | Tech debt, future |

---

## Phase Summary

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1-9 | ✅ COMPLETE | TypeDB, MCP, UI, E2E |
| Phase 10 | ✅ COMPLETE | Architecture Debt |
| Phase 11 | ✅ COMPLETE | Data Integrity |
| Phase 12 | ✅ COMPLETE | Agent Orchestration |

> Details: [R&D-BACKLOG.md](docs/backlog/R&D-BACKLOG.md)

---

## Test Status

| Suite | Count | Status |
|-------|-------|--------|
| Full Suite | 1,106+ | ✅ Passing |
| E2E CRUD | 20 | ✅ |
| Skipped | 46 | ⏸️ |

> Run: `python -m pytest tests/ -v`

---

## R&D Tasks In Progress

| ID | Task | Status | Notes |
|----|------|--------|-------|
| RD-INTENT | Session Intent Reconciliation | DONE | All 4 phases complete |
| RD-INFRA | Infrastructure Health Backend | DONE | Handlers working, E2E validated |
| RD-WORKFLOW | Agentic Workflow Integrity | DONE | All 4 phases complete |
| RD-WORKSPACE | Multi-Agent Workspace Split | PHASE 4 | Phase 4 complete (2026-01-11) |

### RD-INTENT: Session Intent Reconciliation (DONE)

**Status:** Implementation complete (2026-01-11) | **Evidence:** [RD-INTENT-DESIGN-2026-01-10.md](evidence/RD-INTENT-DESIGN-2026-01-10.md)

**Problem:** Claude sessions lose context continuity. Need mechanism to:
- Query previous session intents via claude-mem
- Validate current session aligns with prior work
- Detect "intent drift" across sessions

**Design Completed (2026-01-10):**
- Intent capture format (start + end)
- Reconciliation algorithm (alignment scoring)
- AMNESIA detection (missing handoffs)
- Integration points (healthcheck, hooks, MCP)

**Implementation Progress:**
- [x] Phase 1: Evidence format extension (2026-01-10)
  - `SessionIntent`, `SessionOutcome` dataclasses
  - `capture_intent()`, `capture_outcome()` methods
  - Markdown rendering with intent/outcome sections
- [x] Phase 2: MCP tool enhancement (2026-01-10)
  - `session_capture_intent` - captures goal, source, planned_tasks
  - `session_capture_outcome` - captures status, achieved/deferred tasks, handoffs
  - Auto-reconciliation: completion rate, untracked tasks, planned not done
  - New module: `governance/mcp_tools/sessions_intent.py` (176 lines)
- [x] Phase 3: Healthcheck integration (2026-01-10)
  - New module: `.claude/hooks/checkers/intent_checker.py` (270 lines)
  - Parses SESSION-*.md files for intent/outcome data
  - Shows "Session Continuity" section in detailed healthcheck output
  - Displays handoff items and continuity recommendations
- [x] Phase 4: AMNESIA detection alerts (2026-01-11)
  - New functions: `reconcile_intent()`, `detect_amnesia()`, `format_amnesia_alert()`
  - Healthcheck integration: displays alert when previous session has unhandled handoffs
  - Severity levels: WARNING (1-2 handoffs), ALERT (3+ or PARTIAL status)

### RD-WORKFLOW: Agentic Workflow Integrity (DONE)

**Status:** Implementation complete (2026-01-11) | **Evidence:** [RD-WORKFLOW-DESIGN-2026-01-11.md](evidence/RD-WORKFLOW-DESIGN-2026-01-11.md)

**Problem:** Need gap-based workflow validation to ensure governance rules are followed.

**Implementation Progress:**
- [x] Phase 1: Workflow validation model (2026-01-11)
  - Data structures: `ValidationResult`, `GapTransition`
  - Gap state transition validation
  - Resolution rules matrix (RULE-020, RULE-023, RULE-016)
- [x] Phase 2: Core validation functions (2026-01-11)
  - `validate_gap_transition()` - validates state changes
  - `validate_session_start()` - checks RULE-024 compliance
  - `validate_session_end()` - checks RULE-001 compliance
- [x] Phase 3: Healthcheck integration (2026-01-11)
  - New module: `.claude/hooks/checkers/workflow_checker.py`
  - Shows "Workflow Compliance" section in detailed output
  - Displays compliance status and any violations
- [x] Phase 4: Reporting & alerts dashboard (2026-01-11)
  - New view: `agent/governance_ui/views/workflow_view.py`
  - Navigation item "Workflow" with mdi-check-decagram icon
  - State variables for compliance status, checks, violations
  - Data loader in `controllers/data_loaders.py`

### RD-WORKSPACE: Multi-Agent Workspace Split (Phase 4 Complete)

**Status:** Phase 4 complete (2026-01-11) | **Evidence:** [AGENT-WORKSPACES.md](docs/architecture/AGENT-WORKSPACES.md)

**Problem:** Need specialized agent workspaces with composable skills and wisdom for task delegation.

**Roadmap (from AGENT-WORKSPACES.md):**
- [x] Phase 1: Foundation (MCP split, task CRUD, evidence collection)
- [x] Phase 2: Workspace Setup (2026-01-11)
  - 4 workspaces created: research, coding, curator, sync
  - Each has CLAUDE.md (agent persona, constraints)
  - Each has .mcp.json (subset of MCP servers)
  - 12 skill definitions (3 per workspace)
- [x] Phase 3: Skill System (2026-01-11)
  - Added rule-tags, applicable-roles to TypeDB schema
  - MCP tool: governance_query_rules_by_tags (filter by tags/role)
  - MCP tool: governance_get_agent_wisdom (compose wisdom for role)
  - New module: governance/skill_composer.py (skill composition engine)
  - Fixed mermaid diagram rendering (RULE-039 compliance)
- [x] Phase 4: Delegation Protocol (2026-01-11)
  - TaskHandoff dataclass with markdown serialization
  - governance/orchestrator/handoff.py (evidence handoff format)
  - governance/orchestrator/launcher.py (workspace launcher)
  - MCP tools: governance_create_handoff, governance_get_pending_handoffs
  - MCP tool: governance_route_task_to_agent (task routing by role)
  - Added QA agent workspace (5th workspace with testing heuristics)
  - Added claude-mem to .mcp.json for AMNESIA fallback
- [ ] Phase 5: Optimization Loop
  - Evidence pattern analyzer
  - Rule proposal workflow
  - Trust-weighted voting

---

*Per RULE-024: AMNESIA Protocol - recovery-friendly documents*
*Backlog managed by governance MCP tools*
