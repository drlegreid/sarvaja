# UI-First Platform Sprint (P10) Workflow

## Purpose

Systematic approach to building the Sim.ai Platform UI using **DSM + TDD + EXPLORATORY** fusion methodology.

**Target:** Uncover UI gaps → Implement → Update tests → Ship verified code

---

## Workflow Modes

Choose workflow mode based on project conditions:

```
┌────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW MODE SELECTION                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CONDITIONS                          │  MODE                            │
│  ─────────────────────────────────────────────────────────────────────  │
│  Unknown requirements                │  EXPLORATORY-FIRST               │
│  Legacy system / discovery phase     │  (Explore → Gaps → Implement)    │
│  External dependencies               │                                   │
│  ─────────────────────────────────────────────────────────────────────  │
│  Known domain model                  │  SPEC-FIRST TDD                  │
│  Full control over stack             │  (Spec → Tests → Implement)      │
│  Clear CRUD operations               │                                   │
│  "We have all the controls"          │  ← PREFERRED when applicable     │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### Spec-First TDD Mode (RECOMMENDED for Sim.ai)

```
SPEC-FIRST TDD CYCLE:

1. ENTITY SPEC (DSM)
   └── Define fields, operations, UI views in ENTITY-API-UI-MAP.md

2. API CONTRACT
   └── Write OpenAPI schema / response types

3. POM STRUCTURE
   └── Design Page Objects with data-testid locators

4. RED: Write ALL Failing Tests
   └── Robot tests for every CRUD operation per entity
   └── Tests define the complete UI contract

5. GREEN: Implement to Pass
   └── Build UI components to satisfy tests
   └── Minimum code to pass

6. REFACTOR
   └── Clean up, optimize
   └── No new functionality

7. VERIFY
   └── Full test suite green
   └── Exploratory validation

Benefits:
• Complete specification before implementation
• Test harness validates UI contract
• Predictable execution (no surprises)
• Implementation becomes mechanical
```

---

## Core Principles

### Principle 1: Traceability
```
EVERY UI ELEMENT must trace to:
1. A DOMAIN ENTITY (DSM layer)
2. An API ENDPOINT (Data layer)
3. A TEST CASE (TDD layer)
4. An EXPLORATION SESSION (Discovery layer)
```

### Principle 2: Gaps Before Implementation (Exploratory Mode)
```
NO CODE UNTIL GAPS ARE DOCUMENTED

Workflow Gate:
1. EXPLORE current UI state
2. DOCUMENT all gaps as GAP-UI-XXX
3. REVIEW gap backlog with stakeholder
4. PRIORITIZE which gaps to fix
5. THEN implement (TDD cycle)

Anti-pattern: Writing code before knowing what's broken
```

### Principle 3: Page Object Model (POM)
```
ALL UI code MUST use Page Object Model pattern:

┌─────────────────────────────────────────────────────────────────┐
│                    Page Object Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tests (Robot/Pytest)                                           │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Page Objects (OOP)                                      │    │
│  │  • RulesPage: list_rules(), view_rule(id), edit_rule()  │    │
│  │  • SessionPage: browse(), search(), view_detail()       │    │
│  │  • Components: Navbar, Sidebar, Table, Form, Modal      │    │
│  └─────────────────────────────────────────────────────────┘    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Locators (Selectors)                                    │    │
│  │  • Centralized element selectors                         │    │
│  │  • Easy to update when UI changes                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│       │                                                          │
│       ▼                                                          │
│  Browser / Trame UI                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Benefits:
• Composability: Reuse page methods across tests
• Maintainability: Change locator once, all tests updated
• Readability: Tests read like user stories
• OOP: Inheritance for shared behavior (BasePage)
```

### Principle 4: Test What You Ship (RULE-023)
```
NO SHIPPING UNTESTED CODE

Before claiming "done":
• L1: Import test passes
• L2: Init test passes
• L3: Smoke test passes
• L4: Edge case tests pass
```

---

## Phase 1: DSM (Domain-Specific Model)

### Entity-View Matrix

| Domain Entity | TypeDB Type | API Endpoint | UI View | Priority |
|--------------|-------------|--------------|---------|----------|
| **Rule** | `governance-rule` | `/api/rules` | Rules Browser | P0 |
| **Decision** | `strategic-decision` | `/api/decisions` | Decisions List | P0 |
| **Session** | `session` | `/api/sessions` | Session Browser | P0 |
| **Task** | `task-item` | `/api/tasks` | Task Manager | P1 |
| **Agent** | `agent` | `/api/agents` | Agent Manager | P1 |
| **Evidence** | `evidence-artifact` | `/api/evidence` | Evidence Explorer | P1 |
| **Thought** | `thought-stream` | `/ws/thoughts` | Thought Stream | P2 |
| **Trust** | `agent-trust` | `/api/trust` | Trust Dashboard | P2 |

### Entity Operations (CRUD+)

```yaml
per_entity:
  - CREATE: Form to add new entity
  - READ: List view + Detail view
  - UPDATE: Edit form + Inline edit
  - DELETE: Soft delete with confirmation
  - SEARCH: Filter + Full-text search
  - RELATE: Link to related entities
  - HISTORY: Audit trail / changelog
```

### DSM → UI Mapping

```
Entity: governance-rule
├── List View
│   ├── Columns: [rule_id, title, status, category, priority]
│   ├── Filters: [status, category]
│   ├── Sort: [rule_id, title, updated_at]
│   └── Actions: [view, edit, deprecate]
├── Detail View
│   ├── Header: rule_id + title
│   ├── Metadata: status, category, priority, created_at
│   ├── Content: full directive markdown
│   ├── Relations: related rules, decisions, sessions
│   └── Actions: [edit, deprecate, view_history]
└── Form View
    ├── Fields: [rule_id, title, directive, category, priority]
    ├── Validation: [required, format, uniqueness]
    └── Actions: [save, cancel, preview]
```

---

## Phase 2: TDD (Test-Driven Development)

### Test Pyramid for UI

```
                    ┌─────────────┐
                    │   E2E (5%)  │  ← Playwright + Robot
                   ┌┴─────────────┴┐
                   │ Integration   │  ← API + UI contracts
                   │    (15%)      │
                  ┌┴───────────────┴┐
                  │   Unit (80%)    │  ← Component tests
                  └─────────────────┘
```

### TDD Cycle per Feature

```
1. RED:    Write failing test (Robot Framework)
2. GREEN:  Implement minimum to pass
3. REFACTOR: Clean up, no new functionality
4. EXPLORE: Run exploratory heuristics
5. GAPS:   Document discovered gaps
6. REPEAT: Back to RED for next feature
```

### Test Categories

| Category | Tool | Scope | When |
|----------|------|-------|------|
| `smoke` | Robot | Critical paths only | Every commit |
| `functional` | Robot | All features | PR merge |
| `exploratory` | Playwright MCP | Gap discovery | Sprint start |
| `regression` | Robot | All tests | Release |
| `a11y` | Lighthouse | Accessibility | Weekly |

---

## Phase 3: EXPLORATORY (Playwright MCP + Heuristics)

### Heuristic Matrix

| Heuristic | Purpose | Actions | Artifacts |
|-----------|---------|---------|-----------|
| `page_structure` | Map page elements | snapshot, evaluate | Element tree |
| `navigation_flow` | Test all routes | click, navigate | Route coverage |
| `form_discovery` | Find/test forms | type, submit | Validation rules |
| `data_binding` | Verify data loads | snapshot, compare | Data diff |
| `error_states` | Trigger errors | invalid input | Error catalog |
| `empty_states` | Test no-data | clear filters | Empty state UI |
| `loading_states` | Test async | slow network | Spinner coverage |
| `responsive` | Test breakpoints | resize | Breakpoint issues |
| `crud_cycle` | Full CRUD path | create→read→update→delete | CRUD coverage |

### Exploration Session Template

```yaml
exploration_session:
  id: "EXP-P10-001"
  date: "2024-12-25"
  target_view: "Rules Browser"
  entity: "governance-rule"
  api_endpoints:
    - GET /api/rules
    - GET /api/rules/{id}
    - POST /api/rules

  heuristics_applied:
    - page_structure
    - navigation_flow
    - data_binding
    - crud_cycle

  steps: []  # Filled by LLM exploration

  gaps_discovered:
    - gap_id: "GAP-UI-001"
      type: "missing_feature"
      description: "No edit button for rules"
      severity: "HIGH"
      entity: "governance-rule"
      operation: "UPDATE"

  tests_generated:
    - "tests/ui/rules_browser.robot"
```

### Gap Discovery Protocol

```
For each Entity:
  1. NAVIGATE to entity list view
  2. SNAPSHOT page structure
  3. COMPARE against DSM spec:
     - [ ] List view exists?
     - [ ] All columns present?
     - [ ] Filters work?
     - [ ] Sort works?
     - [ ] Pagination works?
  4. TEST each CRUD operation:
     - [ ] CREATE: Form exists? Validation works?
     - [ ] READ: Detail view exists? All fields shown?
     - [ ] UPDATE: Edit works? Saves correctly?
     - [ ] DELETE: Confirmation? Soft delete?
  5. TEST relations:
     - [ ] Can navigate to related entities?
     - [ ] Relationships displayed?
  6. DOCUMENT gaps as GAP-UI-XXX
  7. GENERATE Robot tests for working features
```

---

## Phase 4: API → UI Contract

### Contract Verification

```
API Response:
{
  "rule_id": "RULE-001",
  "title": "Session Evidence Logging",
  "status": "ACTIVE",
  "category": "governance"
}

UI Must Display:
┌─────────────────────────────────────────┐
│ RULE-001                         ACTIVE │
│ Session Evidence Logging                │
│ Category: governance                    │
└─────────────────────────────────────────┘

Contract Test:
- GET /api/rules → response.rules[0].rule_id shown in UI
- Field mapping verified
- No data loss between API → UI
```

### API Health → UI State

| API State | UI State | Test |
|-----------|----------|------|
| 200 + data | Show data | Happy path |
| 200 + empty | Empty state | No data message |
| 401 | Auth redirect | Login flow |
| 403 | Permission error | Error message |
| 404 | Not found | 404 page |
| 500 | Server error | Error banner |
| Timeout | Loading timeout | Retry option |

---

## Phase 5: Robot Framework Integration

### Test Structure

```
tests/
├── ui/
│   ├── resources/
│   │   ├── common.resource      # Common keywords
│   │   ├── rules.resource       # Rules-specific
│   │   └── variables.py         # Test data
│   ├── rules_browser.robot      # Rules view tests
│   ├── decisions_list.robot     # Decisions view tests
│   ├── session_browser.robot    # Sessions view tests
│   └── smoke.robot              # Critical path smoke
├── api/
│   └── contracts.robot          # API contract tests
└── exploratory/
    └── sessions/                # Exploration session logs
```

### Generated Test Example

```robot
*** Settings ***
Library    Browser
Resource   resources/common.resource

*** Test Cases ***
Rules List Should Show All Rules
    [Tags]    smoke    rules    generated
    [Documentation]    Generated from EXP-P10-001

    Given I Am On The Governance Dashboard
    When I Click The Rules Tab
    Then I Should See The Rules List
    And Each Rule Should Have ID And Title
    And Status Badge Should Be Visible

Rule Detail Should Show Full Content
    [Tags]    functional    rules    generated

    Given I Am On The Rules List
    When I Click On Rule "RULE-001"
    Then I Should See Rule Details
    And Directive Content Should Be Visible
    And Related Decisions Should Be Listed
```

---

## Sprint Execution Flow

### Mode A: Spec-First TDD Sprint (RECOMMENDED)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SPEC-FIRST TDD SPRINT                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  PHASE 1: SPECIFICATION (Before coding)                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Complete ENTITY-API-UI-MAP.md for all sprint entities        │    │
│  │  2. Define API contracts (request/response schemas)              │    │
│  │  3. Design Page Object structure with locators                   │    │
│  │  4. Write ALL Robot tests (RED - all failing)                    │    │
│  │     └── tests/ui/{entity}_crud.robot for each entity             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  PHASE 2: IMPLEMENTATION (Mechanical execution)                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  For each entity (priority order):                               │    │
│  │     1. Implement API endpoint                                    │    │
│  │     2. Implement UI component with data-testid                   │    │
│  │     3. Run tests → GREEN                                         │    │
│  │     4. Refactor (no new functionality)                           │    │
│  │     5. Commit when entity tests pass                             │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  PHASE 3: VERIFICATION                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Full test suite: robot --include smoke,functional            │    │
│  │  2. Quick exploratory validation (Playwright MCP)                │    │
│  │  3. GitHub certification test run                                │    │
│  │  4. Ship                                                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  KEY INSIGHT: Tests are written ONCE upfront, implementation is         │
│  purely mechanical "make the tests pass" work.                          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mode B: Exploratory-First Sprint (Legacy/Discovery)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    EXPLORATORY-FIRST SPRINT                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  DAY 1: DSM + EXPLORE                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Define entity-view matrix for sprint scope                   │    │
│  │  2. Run exploratory session on current UI                        │    │
│  │  3. Document all gaps as GAP-UI-XXX                             │    │
│  │  4. Prioritize gaps by entity importance                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  DAY 2-4: TDD IMPLEMENTATION                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  For each gap (priority order):                                  │    │
│  │     1. Write Robot Framework test (RED)                          │    │
│  │     2. Implement UI feature (GREEN)                              │    │
│  │     3. Refactor + verify (REFACTOR)                              │    │
│  │     4. Quick explore to verify (EXPLORE)                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                          │
│                               ▼                                          │
│  DAY 5: VERIFY + SHIP                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  1. Run full test suite (robot --include smoke,functional)       │    │
│  │  2. Run final exploratory session                                │    │
│  │  3. Update gap tracker (close resolved, add new)                 │    │
│  │  4. GitHub certification test run (STRATEGIC workflow)           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Validation Checklist

### Per Entity

- [ ] DSM spec documented
- [ ] API endpoints identified
- [ ] List view implemented + tested
- [ ] Detail view implemented + tested
- [ ] CRUD operations working
- [ ] Robot tests passing
- [ ] No open GAP-UI-XXX for entity

### Per Sprint

- [ ] All P0 entities complete
- [ ] Smoke tests passing
- [ ] Exploratory session completed
- [ ] Gaps documented and prioritized
- [ ] GitHub certification posted

---

## Related Rules

- **RULE-004**: Exploratory Test Automation (Heuristics)
- **RULE-019**: UI/UX Design Standards (Trame/Vuetify)
- **RULE-020**: LLM-Driven E2E Test Generation (Pipeline)
- **RULE-023**: Test Before Ship (Quality gate)

---

*Created: 2024-12-25*
*Per UI-First Platform Pivot (P10)*
