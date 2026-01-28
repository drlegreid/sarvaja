# TEST-FIX-01-v1: Fix Validation Protocol

**Category:** `quality` | **Priority:** CRITICAL | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** RULE-037
> **Location:** [RULES-STANDARDS.md](../operational/RULES-STANDARDS.md)
> **Tags:** `quality`, `validation`, `fixes`, `evidence`

---

## Directive

When marking a fix as DONE/RESOLVED, agent MUST run verification test and include evidence. "Done but broken" is a CRITICAL violation.

---

## Validation Steps (REQUIRED)

1. **RUN verification test** - Execute test that proves fix works
2. **INCLUDE evidence** - Screenshot, log output, or test result
3. **LINK to fix** - Reference the commit/file changed
4. **SAVE session context** - `chroma_save_session_context()` with fix details

---

## Evidence Requirements

| Fix Type | Verification | Evidence |
|----------|-------------|----------|
| Container fix | `podman ps` shows running | Terminal output |
| MCP fix | `health_check()` OK | Health check output |
| API fix | pytest or Robot test passing | Test result |
| UI fix | Playwright screenshot (Robot/pytest) | Screenshot file |
| Robot test fix | `robot --dryrun` + actual run | Robot report.html |

---

## Anti-Patterns (PROHIBITED)

| Don't | Do Instead |
|-------|-----------|
| Mark DONE without testing | Run verification first |
| "Fixed, should work now" | "Fixed, verified with [test]" |
| Skip evidence for "simple" fixes | ALL fixes need evidence |
| Trust previous session claims | RE-verify in current session |

---

## GAP Trigger

Per GAP-VERIFY-001: Failure to verify results in gap reopening.

---

## Enforcement

**MCP Tool**: `governance_verify_completion(task_id, verification_method, evidence, test_passed)`

This tool enforces verification before marking tasks as completed:
- Requires verification method (how you tested)
- Requires evidence (what you saw)
- Blocks completion if test_passed=False
- Records verification in TypeDB

**Usage**:
```python
governance_verify_completion(
    task_id="GAP-UI-001",
    verification_method="pytest tests/test_ui.py -v",
    evidence="5 tests passed, UI renders correctly",
    test_passed=True
)
```

## Test Coverage

**4 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/session_sync_todos.robot` | unit |
| `tests/robot/unit/sessions_date_bug.robot` | unit |
| `tests/robot/unit/task_commit_link.robot` | unit |
| `tests/robot/unit/task_session_link.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TEST-FIX-01-v1 tests/robot/
```

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
