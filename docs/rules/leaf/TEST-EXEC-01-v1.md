# TEST-EXEC-01-v1: Split Test Execution

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `testing`, `execution`, `performance`, `feedback`

---

## Directive

Test suites MUST be executed in split groups for faster feedback. Full test runs that exceed 60 seconds SHOULD be split into logical groups.

---

## Test Group Structure

| Group | Pattern | Purpose | Max Time |
|-------|---------|---------|----------|
| **Unit** | `tests/test_*_unit.py` or `-k unit` | Fast unit tests | 30s |
| **MCP** | `tests/test_mcp*.py` | MCP tool tests | 60s |
| **Integration** | `tests/test_*_integration.py` | Service integration | 120s |
| **E2E** | `tests/test_*_e2e.py` | End-to-end tests | 300s |

---

## Execution Commands

```bash
# Quick feedback: pytest unit only (fastest - ~3s)
.venv/bin/python3 -m pytest tests/unit/ --report-compressed --tb=no

# Full pytest (all scopes - ~70s)
.venv/bin/python3 -m pytest tests/ --report-compressed --tb=short

# Robot Framework (E2E + integration)
robot --include e2e tests/robot/
robot --include integration tests/robot/

# By domain
.venv/bin/python3 -m pytest -m rules tests/
robot --include rules tests/robot/
```

---

## Report Modes (EPIC-TEST-COMPRESS-001)

Always use `--compressed-summary` for LLM-optimized output via holographic store:

| Flag | Output | Use Case |
|------|--------|----------|
| `--compressed-summary` | `[HOLOGRAPHIC-SUMMARY]` zoom=1 via store | **Default for Claude Code** |
| `--report-compressed` | `[PASS] 1197/1200 (100%) \| 2.1s` | Legacy compressed output |
| `--report-minimized` | Trace-minimized failures | Debugging failures |
| `--report-cert` | JSON evidence in `results/` | CI/CD certification |
| `--report-minimal` | Dots only (. F S) | Lowest context |

**Holographic store auto-populates on every pytest run** (no flag needed for collection).
The `--compressed-summary` flag controls whether the summary is printed at session end.
After any run, query `test_evidence_query(zoom=1)` for context-efficient results.
Per TEST-HOLO-01-v1: zoom 1 → 2 → 3 escalation on failure investigation only.

---

## Framework Split (Per TEST-STRUCT-01-v1 Section 4)

| Scope | Framework | Command |
|-------|-----------|---------|
| Unit | **pytest only** | `pytest tests/unit/` |
| E2E | **Robot only** | `robot --include e2e tests/robot/` |
| Integration | **Robot preferred** | `robot --include integration tests/robot/` |
| Browser | **Robot + Browser** | `robot --include browser tests/robot/e2e/` |

Do NOT run unit tests in Robot Framework -- pytest is the canonical unit test runner.

---

## Skip Configuration

Optional dependencies SHOULD use `pytest.mark.skipif`:

```python
# Example: kanren is optional
pytestmark = pytest.mark.skipif(
    not KANREN_AVAILABLE,
    reason="kanren not installed - optional dependency"
)
```

---

## Validation

- [ ] Unit tests complete in <30s (`pytest tests/unit/`)
- [ ] Optional dependency tests skip gracefully
- [ ] CI runs groups in parallel where possible
- [ ] `--report-compressed` used for all LLM-facing test output
- [ ] No pytest↔Robot duplication for same scope

---

*Per TEST-COMP-02-v1: Test Coverage Protocol*
