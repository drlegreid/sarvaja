# TEST-DATA-01-v1: Test Data Sandbox Isolation

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `testing`, `data-isolation`, `sandbox`, `cleanup`, `test-pyramid`

---

## Directive

All test-created entities MUST be isolated in a dedicated sandbox workspace (`WS-TEST-SANDBOX`) and cleaned up atomically per test case. Production workspace (`WS-9147535A`) MUST NEVER be written to by any test at any tier.

This applies to the full test pyramid AND the test tool triad:

| Tier | Tool | Isolation |
|------|------|-----------|
| 1 Unit | pytest | Mocks only — no real entities |
| 2 Integration | pytest | `TaskTestFactory` + `WS-TEST-SANDBOX` |
| 3 E2E Browser | Robot Framework | `${TEST_WORKSPACE}` + per-case teardown |
| 3 E2E Browser | Playwright MCP | REST API + `workspace_id` + cleanup |

---

## Requirements

### R1: Workspace Isolation

| Requirement | Detail |
|-------------|--------|
| Production workspace | `WS-9147535A` — NEVER written by tests |
| Sandbox workspace | `WS-TEST-SANDBOX` — ALL test entities here |
| Sandbox project | `sarvaja-test` — mirrors production bindings |
| Constant source | `tests/shared/task_test_factory.py:TEST_WORKSPACE_ID` |

### R2: Entity ID Prefix Enforcement

All test-created entities MUST use an ID prefix from `ALL_TEST_PREFIXES`:

```python
ALL_TEST_PREFIXES = [
    "E2E-", "E2E-QUAL-", "RF-QUAL-", "INTTEST-", "CRUD-",
    "TEST-", "AGENT-TEST-", "UI-TEST-", "VERIFY-TEST-",
    "LINK-TEST-", "TASK-TEST-", "SESSION-TEST-", "E2E-TEST-",
    "TODO-",  # Added: catch auto-generated IDs
]
```

`TaskTestFactory.create()` MUST validate the prefix or raise `ValueError`.

### R3: Atomic Test Data Lifecycle

Every test that creates an entity MUST delete it, regardless of pass/fail:

```python
# pytest — factory pattern (CORRECT)
def test_example(task_factory):
    t = task_factory.create(summary="E2E > Atomic > Test")
    assert t.task_id.startswith("E2E-")
    # Auto-deleted by fixture teardown (pass or fail)
```

```robot
# Robot Framework (CORRECT)
Test Create And Verify Task
    [Setup]    ${TASK_ID}=    Create Test Task    summary=RF > Atomic > Test
    Verify Task Exists    ${TASK_ID}
    [Teardown]    Delete Test Task    ${TASK_ID}
```

```javascript
// Playwright (CORRECT)
const taskId = await createTestTask(page, { summary: "PW > Test" });
try { /* assertions */ }
finally { await deleteTestTask(page, taskId); }
```

### R4: Safety Net (Defense in Depth)

Module-scoped `sweep_orphans_after_module` fixture MUST run as autouse to catch entities that escaped per-test cleanup (crashed tests, unhandled exceptions).

Sweep scope: `WS-TEST-SANDBOX` only. Never purge from production workspace.

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Create tasks in `WS-9147535A` from tests | Always pass `workspace_id=TEST_WORKSPACE_ID` |
| Use auto-generated IDs without prefix | Use `TaskTestFactory` or explicit prefixed ID |
| Rely only on module-level cleanup | Per-test teardown + module safety net |
| Hardcode `workspace_id` in each test | Import `TEST_WORKSPACE_ID` from shared constants |
| Skip cleanup in Playwright tests | Always include `finally` block with DELETE call |
| Leave Robot teardown empty | Always `[Teardown] Delete Test Task` |

---

## Heuristic Check

**H-TEST-DATA-001**: Flag any integration or E2E test file that calls `POST /api/tasks` or `task_create()` without:
1. Using `TaskTestFactory`, OR
2. Including an explicit `workspace_id=WS-TEST-SANDBOX`, OR
3. Having a matching `DELETE` / cleanup call

**H-TEST-DATA-002**: Flag any entity in `WS-9147535A` whose ID matches `ALL_TEST_PREFIXES`. These are leaked test data.

---

## Cross-References

- **TEST-FIXTURE-01-v1**: Production-faithful fixtures (field coverage)
- **TEST-E2E-01-v1**: 3-tier mandatory validation
- **WORKFLOW-RD-01-v1**: Autonomous cleanup of TEST-* entities
- **Spec**: `docs/backlog/specs/TEST-DATA-ISOLATION-01.gherkin.md`

---

*Root cause: P13 Playwright E2E revealed TODO-20260324-* entities in production workspace. These were created by tests without sandbox isolation or cleanup.*
