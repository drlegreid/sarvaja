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
# Quick feedback (unit + MCP)
pytest tests/ -k "unit" --timeout=30
pytest tests/test_mcp*.py --timeout=60

# Integration (parallel)
pytest tests/ -k "integration" --timeout=120

# Full suite (split)
pytest tests/test_session*.py tests/test_mcp*.py -v
pytest tests/test_governance*.py tests/test_typedb*.py -v
pytest tests/test_*_e2e.py -v
```

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

- [ ] No single test file takes >30s to complete
- [ ] Optional dependency tests skip gracefully
- [ ] CI runs groups in parallel where possible
- [ ] Local dev gets unit feedback in <30s

---

*Per TEST-COMP-02-v1: Test Coverage Protocol*
