# TASK-VALID-01-v1: Task Completion Validation Protocol

**Category:** `quality` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Location:** [RULES-OPERATIONAL.md](../RULES-OPERATIONAL.md)
> **Tags:** `validation`, `completion`, `quality`, `checklist`
> **Depends:** TEST-FIX-01-v1, TEST-COMP-02-v1, TASK-LIFE-01-v1

---

## Directive

Before marking ANY task as complete, agent MUST verify **integration** not just **existence**. Code that compiles but isn't invoked is NOT complete.

---

## The 5-Point Validation Checklist

| # | Check | Question | Evidence |
|---|-------|----------|----------|
| 1 | **SYNTAX** | Does the code compile/import? | `python3 -c "import module"` |
| 2 | **INVOKE** | Is the code actually called? | Grep for usage, stack trace |
| 3 | **EXECUTE** | Does execution reach the code? | Log output, breakpoint hit |
| 4 | **OUTPUT** | Does it produce expected result? | Test assertion, API response |
| 5 | **PERSIST** | Is the change deployed/saved? | Container restart, git commit |

## DONE Gate (Automated — `task_rules.py:validate_on_complete()`)

The automated DONE gate runs on every `task_update(status="DONE")` and checks:

| # | Field | Requirement | Source |
|---|-------|------------|--------|
| 1 | `linked_sessions` | >= 1 linked session | TypeDB preload |
| 2 | `summary` | Non-empty string | Task entity |
| 3 | `agent_id` | Set AND registered in agent registry | Task entity + agent lookup |
| 4 | `completed_at` | Timestamp auto-set on DONE transition | Task entity |
| 5 | `linked_documents` | >= 1 linked document | TypeDB preload (P14 fix) |

**Preload requirement**: Fields 1 and 5 are fetched from TypeDB at DONE transition time via `_preload_task_from_typedb()`. In-memory cache is NOT sufficient — live TypeDB state is the gate.

**Implementation**: `governance/services/task_rules.py:validate_on_complete()`

---

## Task Type Validation Matrix

| Task Type | SYNTAX | INVOKE | EXECUTE | OUTPUT | PERSIST |
|-----------|--------|--------|---------|--------|---------|
| **New Feature** | Import OK | Called in workflow | Runs without error | Feature works | Git committed |
| **Bug Fix** | Import OK | Fix point reached | Bug no longer occurs | Test passes | Git committed |
| **Refactor** | Import OK | All callers work | No regressions | Tests pass | Git committed |
| **Integration** | Import OK | Wired into system | End-to-end works | E2E test passes | Deployed |
| **Config** | Valid syntax | Config loaded | Settings applied | Behavior changed | Config saved |

---

## Anti-Pattern Detection

| Symptom | Likely Cause | Validation Failed |
|---------|--------------|-------------------|
| "Tests pass but feature doesn't work" | Not invoked in real workflow | INVOKE |
| "Works in tests, fails in production" | Different code path | EXECUTE |
| "Fixed but reverted after restart" | Not persisted | PERSIST |
| "Code exists but nothing changed" | Not wired up | INVOKE |
| "Integration tests skip real paths" | Mock overuse | EXECUTE |

---

## Verification Commands by Category

### Python Code
```bash
# SYNTAX
python3 -c "from module import function"

# INVOKE (check usage)
grep -r "function_name" --include="*.py" | grep -v "def function_name"

# EXECUTE (add logging)
logger.info(f"[VERIFY] function_name called with {args}")

# OUTPUT (run with visible result)
python3 -m pytest tests/test_module.py -v -s

# PERSIST
git diff --name-only
```

### API Endpoints
```bash
# SYNTAX (server starts)
curl http://localhost:8082/api/health

# INVOKE (endpoint registered)
curl http://localhost:8082/api/docs | grep endpoint_name

# EXECUTE (call endpoint)
curl -X GET http://localhost:8082/api/endpoint

# OUTPUT (check response)
curl -s http://localhost:8082/api/endpoint | jq '.expected_field'

# PERSIST (container restart)
podman compose restart governance-dashboard-dev
curl http://localhost:8082/api/endpoint  # Still works
```

### UI Components
```bash
# SYNTAX (no render errors)
podman logs platform_governance-dashboard-dev_1 2>&1 | grep -i error

# INVOKE (component in DOM)
# Use Playwright browser_snapshot

# EXECUTE (interaction works)
# Use Playwright browser_click

# OUTPUT (visual verification)
# Use Playwright browser_take_screenshot

# PERSIST (survives refresh)
# Navigate away and back
```

---

## MCP Tool Usage

```python
# After completing all 5 checks, use task_verify:
task_verify(
    task_id="TASK-001",
    verification_method="5-point checklist: import OK, grep shows 3 callers, logs confirm execution, API returns document_path field, git committed",
    evidence="Test output: 9 passed. API: curl shows document_path. Git: abc123",
    test_passed=True
)
```

---

## Session Completion Gate

Before using `session_end()`, verify:
- [ ] All tasks passed 5-point validation
- [ ] Evidence recorded for each task
- [ ] No "marked complete but not verified" items

---

## Example: TEST-003 Failure Analysis

**Task:** Integrate trace minimization into pytest output
**What happened:** Code written, tests passed, marked complete
**What was missed:**

| Check | Status | Issue |
|-------|--------|-------|
| SYNTAX | PASS | Code imported |
| INVOKE | **FAIL** | Not registered in pytest plugin |
| EXECUTE | **FAIL** | Never called during test runs |
| OUTPUT | **FAIL** | No minimized traces in output |
| PERSIST | N/A | Nothing to persist |

**Root cause:** INVOKE check skipped. Code existed but wasn't wired into pytest_configure.

## Test Coverage

**2 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/data_integrity.robot` | unit |
| `tests/robot/unit/data_integrity_extended.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TASK-VALID-01-v1 tests/robot/
```

---

*Per TEST-FIX-01-v1: Fix Validation Protocol*
*Per TASK-LIFE-01-v1: Task Lifecycle Management*
