# Exploratory Testing Heuristics

> **Gap:** GAP-HEUR-001
> **Rule:** RULE-023 (Test Before Ship)
> **Status:** PARTIAL - Framework created, 16 example tests

---

## GAP-HEUR-001: SFDIPOT/CRUCSS Heuristics Framework

**Problem:** Exploratory tests don't enforce established heuristics for systematic gap discovery

**Required Heuristics:**

| Heuristic | Description | Test Level |
|-----------|-------------|------------|
| **SFDIPOT** | Structure, Function, Data, Interfaces, Platform, Operations, Time | API + UI |
| **CRUCSS** | Capability, Reliability, Usability, Charisma, Security, Scalability | Integration + E2E |
| **HICCUPPS** | History, Image, Claims, Competitors, Procedures, Products, Standards | Acceptance |

---

## SFDIPOT Test Matrix

| Aspect | API Tests | UI Tests | Evidence |
|--------|-----------|----------|----------|
| Structure | Schema validation | Component hierarchy | TypeQL schema |
| Function | Endpoint behavior | User workflows | test_*.py |
| Data | Field validation | Form inputs | data.tql |
| Interfaces | API contracts | Navigation flows | OpenAPI spec |
| Platform | Container health | Browser compat | E2E results |
| Operations | Error handling | User experience | Error logs |
| Time | Response latency | Render performance | metrics.json |

---

## Implementation Requirements

1. Create `tests/heuristics/` directory with heuristic test templates
2. Add `@pytest.mark.heuristic(name="SFDIPOT.Data")` markers to tests
3. Create heuristic coverage report showing which heuristics are tested
4. Integrate with Playwright MCP for UI-level heuristic testing
5. Add data integrity checks (lower layers) and coverage checks (upper layers)

---

## Files Created

- `tests/heuristics/__init__.py`
- `tests/heuristics/sfdipot.py` - SFDIPOT test decorators + fixtures
- `tests/heuristics/crucss.py` - CRUCSS test decorators + fixtures
- `tests/heuristics/coverage_report.py` - Heuristic coverage analyzer

---

## Test Reporting Modes (GAP-TEST-002)

**Status:** IMPLEMENTED

**Usage:**
- `pytest tests/ --report-minimal` - Dots only (`. F S`)
- `pytest tests/ --report-trace` - Full verbose output (-vv)
- `pytest tests/ --report-cert` - JSON evidence to `/results/YYYY-MM-DD/`
- `pytest tests/ --report-cert --results-dir=custom` - Custom output dir

**Files:** `tests/conftest.py` (MinimalReporter, CertificationReporter classes)

---

*Per RULE-023: Test Before Ship*
