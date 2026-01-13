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
| MCP fix | `governance_health()` OK | Health check output |
| API fix | Curl/test passing | Test result |
| UI fix | Playwright screenshot | Screenshot file |

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

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
