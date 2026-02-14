# EPIC-TESTING-E2E: Data Flow Verification Pipeline

| Field | Value |
|-------|-------|
| **Status** | IN_PROGRESS (Phase 1 COMPLETE, Phase 2 SPEC-READY) |
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

### Phase 2: Visual CRUD Verification (Tier 3) — SPEC-READY

**Gherkin Spec**: [E2E-T3-VISUAL-CRUD.gherkin.md](../specs/E2E-T3-VISUAL-CRUD.gherkin.md)

| Task | Status | Gherkin Scenarios | Description | Domain | Priority |
|------|--------|-------------------|-------------|--------|----------|
| E2E-T3-SESSIONS | OPEN | 8 scenarios | **Sessions CRUD**: Create session via form, verify in list, drill into detail, edit description, delete, verify removal. Filter by status/agent/search. Toggle table/pivot view. | UI/sessions | HIGH |
| E2E-T3-RULES | OPEN | 6 scenarios | **Rules Browse & Filter**: Paginate rules table, create rule via form, filter by status/category, search by text, drill into rule detail. | UI/rules | HIGH |
| E2E-T3-TASKS | OPEN | 6 scenarios | **Tasks CRUD**: Create task via form, view detail with linked items, edit status/agent, filter by tab/phase/search. | UI/tasks | HIGH |
| E2E-T3-AGENTS | OPEN | 4 scenarios | **Agents Interaction**: Register agent via dialog, view detail with metrics/trust/controls, toggle pause/resume, verify trust score display. | UI/agents | MEDIUM |
| E2E-T3-DECISIONS | OPEN | 3 scenarios | **Decisions CRUD**: Record decision with options, filter by session, view decision detail with evidence refs. | UI/decisions | MEDIUM |
| E2E-T3-AUDIT | OPEN | 2 scenarios | **Audit Trail**: Browse with entity type/action filters, search by entity ID, verify summary cards. | UI/audit | MEDIUM |
| E2E-T3-NAVIGATION | OPEN | 1 scenario | **Cross-Tab Navigation**: Click all 16 nav items, verify each loads without error, no console errors. | UI/nav | LOW |
| E2E-T3-PROJECTS | OPEN | 1 scenario | **Projects**: Create project, view detail with linked sessions, drill-down navigation. | UI/projects | LOW |
| E2E-T3-CLEANUP | OPEN | 1 scenario | **Test Data Cleanup**: Delete all test artifacts (session, rule, task, decision, agent) via API, verify removal. | testing | LOW |

**Total**: 32 Gherkin scenarios across 9 tasks.

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
- [ ] All Tier 3 tasks: Playwright CRUD interactions per Gherkin specs (32 scenarios)
- [ ] Each scenario produces at least one screenshot evidence artifact
- [ ] Test data cleanup scenario passes (no residual test artifacts)
- [ ] Zero regression in Tier 1 (9,731 unit tests still passing)

## Concerns

- **Container dependency**: Tier 2/3 require running infrastructure (not unit-testable)
- **Playwright MCP**: Use `mcp__playwright__*` tools — no raw Playwright scripts
- **Trame async rendering**: Dashboard renders async; use `browser_wait_for` before assertions
- **Form behavior**: Trame forms may not use standard HTML form patterns; may need `browser_fill_form` or `browser_type` for input

---

*Per TASK-EPIC-01-v1: EPIC-driven task comprehension.*
*Per TEST-E2E-01-v1: Gherkin → EPIC → Playwright execution workflow.*
