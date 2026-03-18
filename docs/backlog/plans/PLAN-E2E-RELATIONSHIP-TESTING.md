# PLAN-E2E-RELATIONSHIP-TESTING: Cross-Entity E2E Test Plan

**Created:** 2026-02-18
**Status:** ACTIVE
**Priority:** HIGH
**Rules:** TEST-TDD-01-v1, TEST-BDD-01-v1, TEST-E2E-01-v1, TEST-SPEC-01-v1, TEST-E2E-FRAMEWORK-01-v1

---

## Objective

Establish comprehensive E2E test coverage that verifies entity relationships are intact across all layers (TypeDB -> API -> UI). Ensure the relationship chain **projects > plans > epics > tasks > sessions > agents > rules > capabilities** is provably working through automated browser + API tests.

After implementation, all future development follows TDD (test-first) workflow.

---

## Current State (2026-02-20)

| Tier | Tests | Status |
|------|-------|--------|
| Unit | 10,290+ | All pass |
| Integration | 141 | All pass (15 skipped) |
| E2E Browser (pytest+Playwright) | 30/32 | 30 pass, 1 xfail (Trame WS), 1 skip |
| E2E API (httpx) | ~70 | Not recently validated |

**Phase 1 progress:** Overlay CSS fix added to conftest (autouse fixture). 29/29 dashboard tests pass. Session detail test marked xfail (Trame WS degradation after 20+ connections — passes in isolation).

**Framework migration:** Migrating from pytest+Playwright to Robot Framework + Browser Library per TEST-E2E-FRAMEWORK-01-v1.

---

## Phase 1: Green Baseline (EPIC-E2E-P1)

**Goal:** Get all existing E2E tests passing.

### Tasks

| Task ID | Description | Files |
|---------|-------------|-------|
| E2E-P1-001 | Add shared `_dismiss_overlays()` fixture to E2E conftest | `tests/e2e/conftest.py` |
| E2E-P1-002 | Fix selectors in `test_session_task_navigation_e2e.py` | `tests/e2e/test_session_task_navigation_e2e.py` |
| E2E-P1-003 | Add missing `data-testid` attributes to UI views if needed | `agent/governance_ui/views/` |
| E2E-P1-004 | Run full E2E suite, verify 100% pass rate | All E2E files |
| E2E-P1-005 | Run httpx API E2E tests, fix any stale response shapes | `tests/e2e/test_governance_crud_e2e.py` etc. |

**Exit criteria:** All E2E tests green (browser + API).

---

## Phase 1.5: Robot Framework Migration (EPIC-E2E-P1.5)

**Goal:** Migrate browser E2E tests from pytest+Playwright to Robot Framework + Browser Library. Apply SRP/DRY/OOP principles per TEST-E2E-FRAMEWORK-01-v1.

### Architecture

```
tests/e2e/robot/
├── suites/                       # .robot test suites by domain (<300 lines)
│   ├── dashboard_navigation.robot
│   ├── rules_view.robot
│   ├── tasks_view.robot
│   ├── sessions_view.robot
│   ├── trust_view.robot
│   ├── agents_view.robot
│   └── infra_view.robot
├── resources/                    # Shared resources
│   ├── common.resource           # Imports, setup/teardown
│   └── selectors.resource        # All data-testid selectors centralized
└── libraries/                    # Python keyword libraries (<300 lines each)
    ├── __init__.py
    ├── actions.py                # Generic: click, wait (Fibonacci backoff), scroll, fill
    ├── navigation.py             # Navigate to tab, verify page loaded
    └── overlay.py                # Vuetify overlay CSS injection
```

### Key Design Patterns

| Pattern | Implementation |
|---------|----------------|
| **Fibonacci Backoff** | `Wait For Element With Backoff` — intervals: 1,1,2,3,5,8,13,21s |
| **Overlay Dismissal** | CSS injection via Suite Setup in common.resource |
| **Safe Click** | Pre-check overlay + click in `actions.py` |
| **Page Object** | Navigation keywords encapsulate tab switching + verification |

### Tasks

| Task ID | Description | Files |
|---------|-------------|-------|
| E2E-P1.5-001 | Install robotframework + robotframework-browser | requirements.txt |
| E2E-P1.5-002 | Create `actions.py` keyword library (click, wait/backoff, scroll, fill) | libraries/actions.py |
| E2E-P1.5-003 | Create `navigation.py` keyword library (tab nav, page verify) | libraries/navigation.py |
| E2E-P1.5-004 | Create `overlay.py` keyword library (Vuetify CSS injection) | libraries/overlay.py |
| E2E-P1.5-005 | Create `selectors.resource` with all data-testid mappings | resources/selectors.resource |
| E2E-P1.5-006 | Create `common.resource` with Suite Setup/Teardown | resources/common.resource |
| E2E-P1.5-007 | Migrate dashboard navigation tests to .robot | suites/dashboard_navigation.robot |
| E2E-P1.5-008 | Migrate rules view tests to .robot | suites/rules_view.robot |
| E2E-P1.5-009 | Migrate tasks/sessions/trust/agents/infra tests to .robot | suites/*.robot |
| E2E-P1.5-010 | Run full Robot Framework suite, verify green baseline | All suites |

**Exit criteria:** All 29 dashboard + navigation tests pass via `robot` command. Old pytest browser tests archived.

---

## Phase 2: Cross-Entity Smoke Test (EPIC-E2E-P2)

**Goal:** Prove all entity relationships work end-to-end with seeded TEST-* data.

### Approach
- Seed TEST-* prefixed entities via API
- Verify cross-links exist in both directions
- Clean up TEST-* data after test run
- Tests are repeatable and safe

### Entity Chain to Test

```
Project (TEST-PROJ-001)
  -> Plan (TEST-PLAN-001)
    -> Epic (TEST-EPIC-001)
      -> Task (TEST-TASK-001)
        -> Rule (TEST-RULE-001) via implements-rule
        -> Session (TEST-SESSION-001) via completed-in
        -> Evidence via evidence-supports
        -> Commit via task-commit
Session (TEST-SESSION-001)
  -> Rule via session-applied-rule
  -> Decision (TEST-DEC-001) via session-decision
Agent (TEST-AGENT-001)
  -> Capabilities list (map to skillsets concept)
  -> Tasks (via agent_id on task)
  -> Sessions (via agent_id on session)
```

### Tasks

| Task ID | Description | Files |
|---------|-------------|-------|
| E2E-P2-001 | Create `test_cross_entity_smoke_e2e.py` with seeded data | `tests/e2e/test_cross_entity_smoke_e2e.py` |
| E2E-P2-002 | Test Project -> Plan -> Epic -> Task containment | Same file |
| E2E-P2-003 | Test Task <-> Rule linking (implements-rule) | Same file |
| E2E-P2-004 | Test Task <-> Session linking (completed-in) | Same file |
| E2E-P2-005 | Test Session <-> Rule linking (session-applied-rule) | Same file |
| E2E-P2-006 | Test Session <-> Decision linking (session-decision) | Same file |
| E2E-P2-007 | Test Agent -> capabilities (skillsets mapping) | Same file |
| E2E-P2-008 | Test bidirectional queries (task's sessions, session's tasks) | Same file |
| E2E-P2-009 | Full chain round-trip: create all, verify all links, clean up | Same file |

**Exit criteria:** Single test file that creates a complete entity graph, verifies all relationships, and cleans up.

---

## Phase 3: Cross-Entity Browser Navigation (EPIC-E2E-P3)

**Goal:** Prove users can navigate between linked entities in the dashboard UI.

### Navigation Paths to Test

```
Sessions tab -> click session row -> detail view -> click task chip -> Tasks view with detail
Tasks tab -> click task row -> detail view -> see linked rule -> click rule -> Rules view
Rules tab -> click rule row -> detail view -> see implementing tasks list
Agents tab -> click agent -> detail view -> see recent sessions
Trust tab -> leaderboard -> click agent -> agent detail
```

### Tasks

| Task ID | Description | Files |
|---------|-------------|-------|
| E2E-P3-001 | Write Gherkin spec for cross-entity navigation | `docs/backlog/specs/E2E-T3-CROSS-NAV.gherkin.md` |
| E2E-P3-002 | Implement session -> task navigation test | `tests/e2e/test_cross_entity_nav_e2e.py` |
| E2E-P3-003 | Implement task -> rule navigation test | Same file |
| E2E-P3-004 | Implement rule -> tasks list test | Same file |
| E2E-P3-005 | Implement agent detail navigation test | Same file |
| E2E-P3-006 | Implement full round-trip navigation test | Same file |

**Exit criteria:** User can navigate the full entity chain through the UI.

---

## Phase 4: Production Data Integrity (EPIC-E2E-P4)

**Goal:** Verify existing production data in TypeDB has correct relationships.

**Delivered as a SEPARATE task after Phases 1-3.**

### Tasks

| Task ID | Description | Files |
|---------|-------------|-------|
| E2E-P4-001 | Write `test_production_data_integrity_e2e.py` | `tests/e2e/test_production_data_integrity_e2e.py` |
| E2E-P4-002 | Verify CLOSED tasks have evidence linkage | Same file |
| E2E-P4-003 | Verify sessions have applied rules | Same file |
| E2E-P4-004 | Verify agents have trust scores | Same file |
| E2E-P4-005 | Report orphaned entities (tasks without sessions, etc.) | Same file |

**Exit criteria:** Production data integrity report with pass/fail for each relationship type.

---

## Phase 5: TDD Enforcement (EPIC-E2E-P5)

**Goal:** Update governance rules to enforce TDD for all future development.

### Tasks

| Task ID | Description | Files |
|---------|-------------|-------|
| E2E-P5-001 | Update TEST-TDD-01-v1: Make E2E TDD MANDATORY (not OPTIONAL) | `docs/rules/leaf/TEST-TDD-01-v1.md` |
| E2E-P5-002 | Update TEST-BDD-01-v1: Enforce Gherkin-first for E2E | `docs/rules/leaf/TEST-BDD-01-v1.md` |
| E2E-P5-003 | Create pre-commit hook that checks test exists before impl | `.claude/hooks/` |
| E2E-P5-004 | Document TDD workflow in CLAUDE.md quick reference | `CLAUDE.md` |

**Exit criteria:** TDD is enforced by rules + tooling for all future development.

---

## Verification Checklist

- [ ] Phase 1: All existing E2E tests pass (browser + API)
- [ ] Phase 2: Cross-entity smoke test creates/verifies/cleans full entity graph
- [ ] Phase 3: Cross-entity navigation works in browser
- [ ] Phase 4: Production data integrity validated
- [ ] Phase 5: TDD rules updated and enforced
- [ ] All new tests follow Gherkin-first BDD pattern (TEST-BDD-01-v1)
- [ ] All phases have evidence in `evidence/` directory

---

## Dependencies

| Rule | Relevance |
|------|-----------|
| TEST-TDD-01-v1 | Red-Green-Refactor methodology |
| TEST-BDD-01-v1 | Gherkin-first for E2E |
| TEST-E2E-01-v1 | 3-tier validation (unit, integration, visual) |
| TEST-SPEC-01-v1 | 3-tier Gherkin specifications |
| TEST-E2E-FRAMEWORK-01-v1 | SRP/DRY/OOP, <300 lines, Fibonacci backoff |
| GOV-MCP-FIRST-01-v1 | MCP tools primary for task management |

---

*Per TASK-EPIC-01-v1: Epic decomposition for complex tasks*
*Per TEST-BDD-01-v1: BDD paradigm for E2E tests*
