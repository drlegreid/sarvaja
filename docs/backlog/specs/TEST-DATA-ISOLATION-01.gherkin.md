# TEST-DATA-ISOLATION-01: Test Data Sandbox Strategy

**Rule:** TEST-DATA-01-v1
**Phase:** Cross-cutting (applies to all EPIC phases)
**Priority:** CRITICAL

---

## Problem Statement

Test entities (e.g., `TODO-20260324-001/002/003`) leak into the production workspace
(`WS-9147535A`) and persist between test runs. Root causes:

1. No dedicated test workspace — all test data shares `WS-9147535A` with delivery items
2. Some test entity IDs (e.g., `TODO-*`) don't match cleanup prefixes in `ALL_TEST_PREFIXES`
3. Not all test tools (pytest, Robot, Playwright) enforce per-case create/delete
4. Cleanup relies on module-scoped teardown — crashed tests leave orphans

## Design

### Workspace Isolation

```
sarvaja-platform (PRODUCTION)        sarvaja-test (SANDBOX)
├── WS-9147535A                      ├── WS-TEST-SANDBOX
│   ├── SRVJ-BUG-018  (real)         │   ├── E2E-TASK-001  (test)
│   ├── SRVJ-FEAT-015 (real)         │   ├── INTTEST-002   (test)
│   └── ... delivery items           │   └── ... ephemeral
│                                    │
│   NEVER written by tests           │   ALWAYS cleaned after each test
```

### Test Tool Triad Coverage

| Tool | Layer | Isolation Mechanism |
|------|-------|---------------------|
| **pytest** (unit) | Tier 1 | Mocks only — no real entities created |
| **pytest** (integration) | Tier 2 | `TaskTestFactory` + `WS-TEST-SANDBOX` + per-test cleanup fixture |
| **Robot Framework** | Tier 3 E2E | `${TEST_WORKSPACE}` variable + `[Teardown] Delete Test Task` keyword |
| **Playwright MCP** | Tier 3 E2E | API calls with `workspace_id=WS-TEST-SANDBOX` + cleanup evaluate |

---

## BDD Scenarios

```gherkin
Feature: Test Data Isolation (TEST-DATA-01-v1)

  Background:
    Given the production workspace is WS-9147535A
    And the test sandbox workspace is WS-TEST-SANDBOX

  # --- Workspace Isolation ---

  Scenario: Integration test creates task in sandbox workspace
    When an integration test creates a task via TaskTestFactory
    Then the task's workspace_id is "WS-TEST-SANDBOX"
    And the task does NOT appear in WS-9147535A task list

  Scenario: Production workspace is never written by tests
    Given 50 integration tests have run
    When I query tasks in WS-9147535A
    Then no task has an ID matching any test prefix in ALL_TEST_PREFIXES

  Scenario: E2E Robot test creates task in sandbox
    Given a Robot Framework test suite with ${TEST_WORKSPACE} = WS-TEST-SANDBOX
    When the test creates a task via POST /api/tasks
    Then workspace_id in the request body is "${TEST_WORKSPACE}"
    And [Teardown] deletes the task by ID

  # --- Atomic Lifecycle ---

  Scenario: Per-test cleanup on success
    Given test "test_create_and_verify" creates task "E2E-ATOMIC-001"
    When the test passes
    Then "E2E-ATOMIC-001" is deleted before the next test runs

  Scenario: Per-test cleanup on failure
    Given test "test_failing_scenario" creates task "E2E-ATOMIC-002"
    When the test fails with AssertionError
    Then "E2E-ATOMIC-002" is still deleted (cleanup runs in finally/teardown)

  Scenario: Orphan safety net catches leaked entities
    Given a test crashed before cleanup ran
    And task "E2E-ORPHAN-001" was left in WS-TEST-SANDBOX
    When the module-level sweep_orphans fixture runs
    Then "E2E-ORPHAN-001" is deleted via purge_test_artifacts()

  # --- Prefix Enforcement ---

  Scenario: All test-created entity IDs must use registered prefix
    When a test calls task_create() without a prefix from ALL_TEST_PREFIXES
    Then TaskTestFactory raises ValueError("Test task IDs must use a registered prefix")

  Scenario: TODO-* prefix is added to test prefix registry
    Given ALL_TEST_PREFIXES includes "TODO-"
    Then cleanup scripts purge TODO-* entities from sandbox workspace

  # --- Cross-Tool Consistency ---

  Scenario: Playwright E2E uses same sandbox workspace
    Given a Playwright test navigates to the dashboard
    When it creates a task via REST API
    Then the request includes workspace_id = "WS-TEST-SANDBOX"
    And the task is deleted in test teardown

  Scenario: MCP session tests use sandbox project
    Given an MCP integration test calls session_start()
    When the session is created
    Then the session topic includes a test prefix
    And the session is ended in teardown
```

---

## Implementation Checklist

### Constants & Config
- [ ] Add `TEST_WORKSPACE_ID = "WS-TEST-SANDBOX"` to `tests/shared/task_test_factory.py`
- [ ] Add `TEST_PROJECT_ID = "sarvaja-test"` to `tests/shared/task_test_factory.py`
- [ ] Add `"TODO-"` to `ALL_TEST_PREFIXES`
- [ ] Add `${TEST_WORKSPACE}` to Robot `common.resource`

### pytest (integration)
- [ ] `TaskTestFactory.__init__()` defaults to `workspace_id=TEST_WORKSPACE_ID`
- [ ] `task_factory` fixture in conftest.py passes `workspace_id=TEST_WORKSPACE_ID`
- [ ] `sweep_orphans_after_module` filters by `TEST_WORKSPACE_ID`

### Robot Framework (E2E)
- [ ] Add `Delete Test Task` keyword to common.resource
- [ ] All task-creating suites use `[Teardown] Delete Test Task ${TASK_ID}`
- [ ] `${TEST_WORKSPACE}` used in all POST /api/tasks calls

### Playwright (E2E)
- [ ] Document: Playwright tests must include cleanup evaluate blocks
- [ ] Pattern: `await page.evaluate(() => fetch('/api/tasks/{id}', {method: 'DELETE'}))`

### Scripts
- [ ] `scripts/purge_test_artifacts.py` adds `--workspace WS-TEST-SANDBOX` filter
- [ ] `scripts/cleanup_test_data.py` scopes to sandbox workspace

---

*Per TEST-E2E-01-v1: Data Flow Verification Protocol*
*Per TEST-FIXTURE-01-v1: Production-Faithful Test Fixtures*
*Per WORKFLOW-RD-01-v1: Autonomous cleanup of TEST-* entities*
