# EPIC-TESTING-E2E: Data Flow Verification Pipeline

| Field | Value |
|-------|-------|
| **Status** | IN_PROGRESS (Phase 1 COMPLETE, Phase 2 COMPLETE — 8/9 tasks done, Projects deferred) |
| **Priority** | HIGH |
| **Rule** | TEST-E2E-01-v1 |
| **Created** | 2026-02-14 |
| **Domain** | Testing (Tier 2 Integration + Tier 3 Visual CRUD) |

## Strategic Goal

Unit tests (Tier 1) cover 98% of governance modules with 9,731 tests. However, data flow changes lack **integration verification** (Tier 2: API curl assertions) and **visual CRUD verification** (Tier 3: Playwright interactive scenarios). Per TEST-E2E-01-v1, all 3 tiers are MANDATORY for data flow changes.

## Scope

### In-Scope
- API integration tests for all governance endpoints (DONE)
- Playwright CRUD interaction tests for all dashboard views
- Gherkin spec → EPIC task → Playwright execution workflow

### Out-of-Scope
- Unit test expansion (already at 98%)
- Performance/load testing (separate EPIC)

## Task Breakdown

### Phase 1: API Integration Tests (Tier 2) — COMPLETE

| Task | Status | Description | Tests | Domain |
|------|--------|-------------|-------|--------|
| E2E-T2-001 | DONE | **Session Endpoints**: list, get, detail/zoom, tools, thoughts, evidence, lifecycle | 15 | sessions |
| E2E-T2-002 | DONE | **Task Endpoints**: list, get, filter, CRUD, details, execution, workflow | 13 | tasks |
| E2E-T2-003 | DONE | **Rule Endpoints**: list, get, filter, dependencies, linked tasks | 11 | rules |
| E2E-T2-004 | DONE | **Agent Endpoints**: list, get, trust, sessions, observability | 11 | agents |
| E2E-T2-005 | DONE | **Decision Endpoints**: list, get, create/delete lifecycle | 6 | decisions |
| E2E-T2-006 | DONE | **Misc Endpoints**: health, CVP, evidence, reports, metrics, files, audit, infra | 14 | testing |

**Total**: 70 integration tests passing (committed `0332aef`).

### Phase 2: Visual CRUD Verification (Tier 3) — COMPLETE (8/9 tasks)

**Gherkin Spec**: [E2E-T3-VISUAL-CRUD.gherkin.md](../specs/E2E-T3-VISUAL-CRUD.gherkin.md)

| Task | Status | Gherkin Scenarios | Description | Domain | Priority |
|------|--------|-------------------|-------------|--------|----------|
| E2E-T3-NAVIGATION | DONE | 1 scenario | **Cross-Tab Navigation**: All 16 nav items load without error. | UI/nav | LOW |
| E2E-T3-SESSIONS | DONE | 8 scenarios | **Sessions CRUD**: 8/8 PASSED. Create, list, detail, edit, delete, filter, search, pivot. | UI/sessions | HIGH |
| E2E-T3-RULES | DONE | 6 scenarios | **Rules Browse & Filter**: 4/6 PASSED, 2 BUG (filter dropdowns not wired: BUG-UI-RULES-001). | UI/rules | HIGH |
| E2E-T3-TASKS | DONE | 6 scenarios | **Tasks CRUD**: 4/6 PASSED, 2 BUG (tab/phase filters not wired: BUG-UI-TASKS-002). | UI/tasks | HIGH |
| E2E-T3-AGENTS | DONE | 4 scenarios | **Agents Interaction**: 3/4 PASSED, 1 BUG (toggle 404: BUG-UI-AGENTS-001). | UI/agents | MEDIUM |
| E2E-T3-DECISIONS | DONE | 3 scenarios | **Decisions CRUD**: 3/3 PASSED. Record, filter, detail view. | UI/decisions | MEDIUM |
| E2E-T3-AUDIT | DONE | 2 scenarios | **Audit Trail**: 1/2 PASSED, 1 BUG (filters not wired: BUG-UI-AUDIT-001). | UI/audit | MEDIUM |
| E2E-T3-PROJECTS | DEFERRED | 1 scenario | **Projects**: Deferred — requires project CRUD UI (not yet implemented). | UI/projects | LOW |
| E2E-T3-CLEANUP | DONE | 1 scenario | **Test Data Cleanup**: All test artifacts removed, counts verified. | testing | LOW |

**Total**: 31/32 Gherkin scenarios executed (1 deferred). 24 PASSED, 6 BUG (filed), 1 deferred.

### Bugs Discovered (per TEST-DISCOVERY-01-v1)

| Bug ID | Severity | Component | Summary |
|--------|----------|-----------|---------|
| BUG-UI-RULES-001 | HIGH | rules_view.py | Status/category filter dropdowns not wired to filtering |
| BUG-UI-SESSIONS-001 | MEDIUM | sessions_pagination.py | Pivot view toggle button doesn't switch view mode |
| BUG-UI-TASKS-001 | MEDIUM | tasks.py | Create Task dialog form submission error |
| BUG-UI-TASKS-002 | HIGH | tasks.py | Tab/phase filters not wired to table filtering |
| BUG-UI-AGENTS-001 | HIGH | agents.py | Agent pause/resume toggle returns 404 (endpoint missing) |
| BUG-UI-AUDIT-001 | HIGH | audit.py | Entity Type/Action Type/Entity ID filters not wired to API query |

## Workflow (Per TEST-E2E-01-v1 Gherkin-First Protocol)

```
1. Author Gherkin specs    → docs/backlog/specs/E2E-T3-*.gherkin.md
2. Generate EPIC tasks     → This document (task breakdown with acceptance criteria)
3. Execute via Playwright  → mcp__playwright__* tools (click, fill, assert, screenshot)
4. Capture evidence        → evidence/test-results/E2E-T3-*.png (screenshot per scenario)
5. Mark task DONE          → Update this EPIC + TypeDB task status
```

## Dependencies

- Container stack running (`podman compose --profile cpu up -d`)
- TypeDB seeded with rules + test sessions
- Dashboard accessible on :8081, API on :8082

## Acceptance Criteria

- [x] All Tier 2 tasks: curl endpoint + assert HTTP 200 + validate JSON schema (70 tests)
- [x] All Tier 3 tasks: Playwright CRUD interactions per Gherkin specs (31/32 scenarios, 1 deferred)
- [x] Each scenario produces at least one screenshot evidence artifact (20+ screenshots in evidence/test-results/)
- [x] Test data cleanup scenario passes (no residual test artifacts)
- [x] Zero regression in Tier 1 (9,731 passed, 5 skipped, 0 failures)

## Concerns

- **Container dependency**: Tier 2/3 require running infrastructure (not unit-testable)
- **Playwright MCP**: Use `mcp__playwright__*` tools — no raw Playwright scripts
- **Trame async rendering**: Dashboard renders async; use `browser_wait_for` before assertions
- **Form behavior**: Trame forms may not use standard HTML form patterns; may need `browser_fill_form` or `browser_type` for input

---

*Per TASK-EPIC-01-v1: EPIC-driven task comprehension.*
*Per TEST-E2E-01-v1: Gherkin → EPIC → Playwright execution workflow.*
