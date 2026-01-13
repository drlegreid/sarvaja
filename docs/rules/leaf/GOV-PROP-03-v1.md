# GOV-PROP-03-v1: Test Data Integrity Requirements

**Category:** `testing` | **Priority:** HIGH | **Status:** DRAFT | **Type:** OPERATIONAL

> **Legacy ID:** RULE-025
> **Location:** [RULES-STRATEGY.md](../technical/RULES-STRATEGY.md)
> **Tags:** `testing`, `data`, `integrity`, `validation`

---

## Directive

All tests MUST include API data validation assertions. A test that passes with empty data is not valid.

---

## Requirements

1. **API Data Validation**: Verify API returns non-empty data
2. **Fail on Empty**: Empty data = test FAIL with diagnostic
3. **Realistic Mocks**: Mocks must return realistic data

---

## Anti-Patterns

| Don't | Do Instead |
|-------|------------|
| `assert isinstance(result, list)` | `assert len(result) > 0` |
| `mock.return_value = []` | `mock.return_value = [realistic_data]` |
| Test imports only | Test actual data display |

---

## Exploratory Test Heuristics

| Heuristic | Implementation |
|-----------|----------------|
| API Data Available | Query API, verify >0 items |
| Data Visible | If API returns data, UI displays it |
| Empty State Handled | UI shows "No data" message |
| CRUD Complete | Create-Read-Update-Delete works |

---

## Validation

- [ ] No tests with empty assertions pass
- [ ] All E2E tests verify data availability first
- [ ] Exploratory tests log findings to GAP-INDEX.md

---

*Per SESSION-DSM-01-v1: DSP Semantic Code Structure*
