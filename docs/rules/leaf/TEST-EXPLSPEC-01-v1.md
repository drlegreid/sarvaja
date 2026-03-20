# TEST-EXPLSPEC-01-v1: Exploratory Dynamic Specification

| Field | Value |
|-------|-------|
| **Rule ID** | TEST-EXPLSPEC-01-v1 |
| **Category** | testing |
| **Priority** | HIGH |
| **Applicability** | MANDATORY |
| **Status** | ACTIVE |
| **Created** | 2026-03-19 |

## Directive

During MCP Playwright exploratory testing, capture a **3-layer Gherkin-style specification** alongside screenshots. This Exploratory Dynamic Spec (EDS) serves as a living PRD from which static Robot Framework, Playwright, and API tests can be decomposed and generated.

## Specification Layers

### Layer 1: Business Intent (Domain / Action / Concern)

Gherkin `Feature` + `Scenario` descriptions expressing what the user wants to achieve. Organized by domain (e.g., Sessions, Rules, Tasks), action (e.g., Navigate, Create, Filter), and concern (e.g., Data visibility, CRUD completion, Error handling).

```gherkin
Feature: Sessions Management
  As a governance operator
  I want to view and filter session evidence
  So that I can audit agent activity

  Scenario: View session list with stats
    Given the dashboard is loaded
    When I navigate to the Sessions view
    Then I should see session stats cards (Total, Active, Duration, Avg Tasks)
    And I should see a filterable session data table
```

### Layer 2: Technical Level 1 — Reusable High-Level Actions

Abstract, reusable actions with intent and parameters. These map to Robot Framework keywords or Playwright helper functions. Categories:

| Action Type | Examples |
|-------------|----------|
| **Navigation** | Navigate To Tab(tab_name), Navigate Back From Detail(selector) |
| **CRUD** | Click Add Button(entity), Fill Form Field(field, value), Submit Form, Delete With Confirm |
| **Interaction** | Click Table Row(index), Toggle Filter(name), Search(query), Select Dropdown(name, value) |
| **Assertion** | Verify Element Visible(testid), Verify Table Has Rows, Verify Stats Card(label, value) |
| **Wait** | Wait For Element With Backoff(selector), Wait For Table Rows |

```gherkin
  Scenario: View session list with stats
    Given I execute "Navigate To Tab" with tab_name="sessions"
    When I execute "Verify Element Visible" with testid="sessions-list"
    Then I execute "Verify Stats Card" with label="Total Sessions" value=">0"
    And I execute "Verify Table Has Rows" with table="sessions-table"
```

### Layer 3: Technical Level 2 — Low-Level Locators and API Contracts

Exact page objects, element locators, and API request/response contracts.

**UI:**
```yaml
Page: Sessions List
  Elements:
    stats_total: "[data-testid='sessions-list'] .text-h4 >> nth=0"
    stats_active: "[data-testid='sessions-list'] .text-h4 >> nth=1"
    filter_status: "[data-testid='sessions-filter-status']"
    filter_agent: "[data-testid='sessions-filter-agent']"
    search_input: "[data-testid='sessions-search']"
    data_table: "[data-testid='sessions-table']"
    first_row: "[data-testid='sessions-table'] tbody tr:has(td) >> nth=0"
    add_btn: "[data-testid='sessions-add-btn']"
    pagination: "[data-testid='sessions-pagination']"
```

**API:**
```yaml
GET /api/sessions:
  Request:
    Headers: { Content-Type: application/json }
    Params: { status: "ACTIVE", limit: 20, offset: 0 }
  Response:
    Status: 200
    Body: [ { session_id: str, status: str, start_time: str, ... } ]

GET /api/sessions/{id}:
  Response:
    Status: 200
    Body: { session_id: str, tool_calls: list, thoughts: list, ... }
```

## MCP Tooling Protocol (MANDATORY)

EDS exploratory testing MUST use the available MCP servers directly — NOT shell wrappers, bare curl, or manual commands.

### 3-MCP Triad

| MCP Server | Purpose in EDS | Key Tools |
|------------|---------------|-----------|
| **playwright** | UI exploration + CRUD interaction | `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`, `browser_take_screenshot`, `browser_wait_for`, `browser_network_requests`, `browser_console_messages` |
| **rest-api** | API contract validation | `test_request` (GET/POST/PUT/DELETE against localhost:8082) — structured response with timing, headers, status |
| **log-analyzer** | Server-side verification | `run_unit_test` (targeted), `analyze_tests`, `search_log_time_based` (check for errors during exploration) |

### EDS Execution Flow

```
1. SETUP
   playwright → browser_navigate(url="http://localhost:8081")
   playwright → browser_snapshot()  ← establishes baseline

2. UI EXPLORATION (per view)
   playwright → browser_click(ref=nav_item)     ← navigate
   playwright → browser_snapshot()               ← capture structure (Layer 2/3 data)
   playwright → browser_take_screenshot(filename="evidence/test-results/EDS-{domain}-{view}.png")
   playwright → browser_fill_form(fields=[...])  ← CRUD interaction
   playwright → browser_network_requests()       ← capture API calls made by UI

3. API VALIDATION (per endpoint)
   rest-api → test_request(method="GET", endpoint="/api/tasks")          ← Layer 3 contract
   rest-api → test_request(method="POST", endpoint="/api/tasks", body={})← mutation test
   rest-api → test_request(method="GET", endpoint="/api/workspaces/{id}/tasks") ← relation query

4. SERVER-SIDE VERIFICATION
   log-analyzer → search_log_time_based(minutes=5, scope="api")  ← check for errors during exploration
   log-analyzer → run_unit_test(agent="tasks")                   ← targeted regression check

5. EVIDENCE RECORDING
   gov-sessions → session_test_result(test_id="EDS-{id}", status="passed|failed")
   gov-sessions → test_evidence_push(test_id="EDS-{id}", fixtures_json="{...}")
```

### Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| `curl http://localhost:8082/api/tasks` | `mcp__rest-api__test_request(method="GET", endpoint="/api/tasks")` |
| `bash: python3 -m pytest tests/` | `mcp__log-analyzer__run_unit_test(agent="tasks")` |
| Screenshot-only validation | `browser_snapshot()` for structure + `browser_take_screenshot()` for evidence |
| Ignore server logs | `search_log_time_based(minutes=5)` after each CRUD operation |

## Output Format

Each exploratory session MUST produce a spec file at:
```
docs/backlog/specs/EDS-{DOMAIN}-{DATE}.eds.md
```

Structure:
```markdown
# EDS: {Domain} — {Date}

## Discovery Context
- URL: http://localhost:8081
- Browser: chromium
- Views explored: [list]

## Layer 1: Business Scenarios
{Gherkin features + scenarios}

## Layer 2: Reusable Actions Catalog
{Action table with parameters}

## Layer 3: Page Objects & API Contracts
{Locators YAML + API request/response specs}

## Screenshots
{Linked evidence screenshots}

## Test Decomposition Plan
{List of static tests to generate from this spec}
```

## Rationale

1. **Screenshots alone are passive** — they don't capture intent or reusable patterns
2. **3-layer decomposition** enables test generation at any granularity
3. **Layer 2 actions** prevent duplication across test suites (DRY)
4. **Layer 3 locators** become the single source of truth for page objects
5. **EDS files** bridge the gap between exploratory testing and systematic test coverage

## Related Rules

- TEST-E2E-01-v1: Data Flow Verification (3-tier mandatory)
- TEST-SPEC-01-v1: 3-Tier Validation Specs
- TEST-BDD-01-v1: BDD E2E Testing Standard
- TEST-E2E-FRAMEWORK-01-v1: Robot Framework Migration
