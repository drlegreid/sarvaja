# TEST-EVID-01-v1: BDD Evidence Collection

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Legacy ID:** N/A (new rule)
> **Location:** [RULES-OPERATIONAL.md](../operational/RULES-OPERATIONAL.md)
> **Tags:** `testing`, `bdd`, `evidence`, `traceability`

---

## Directive

Test runs MUST produce structured BDD evidence with Given/When/Then steps, rule traceability, and session linkage for governance compliance verification.

---

## Implementation

### Evidence Structure

```json
{
  "test_id": "tests/unit/test_auth.py::test_login",
  "name": "test_login",
  "category": "unit",
  "status": "passed",
  "duration_ms": 150.0,
  "intent": "User login with valid credentials succeeds",
  "bdd_steps": [
    {"type": "given", "description": "a registered user exists", "passed": true},
    {"type": "when", "description": "user submits valid credentials", "passed": true},
    {"type": "then", "description": "user receives auth token", "passed": true}
  ],
  "linked_rules": ["RULE-001", "SESSION-EVID-01-v1"],
  "linked_gaps": ["GAP-TEST-EVIDENCE-001"],
  "session_id": "SESSION-2026-01-21-TEST"
}
```

### Usage

```bash
# Enable BDD evidence collection
pytest tests/ --bdd-evidence

# With custom directory
pytest tests/ --bdd-evidence --evidence-dir=custom

# Link to governance session
pytest tests/ --bdd-evidence --session-id=SESSION-2026-01-21-TEST

# Or via environment variable
GOVERNANCE_SESSION_ID=SESSION-2026-01-21-TEST pytest tests/ --bdd-evidence

# Enable session event reporting (GAP-TEST-EVIDENCE-002)
pytest tests/ --session-report

# Combine file evidence + session reporting
pytest tests/ --bdd-evidence --session-report
```

### Session Event Integration (GAP-TEST-EVIDENCE-002)

Test results can be reported as governance session events:

```python
# Via MCP tool
session_test_result(
    test_id="tests/unit/test_auth.py::test_login",
    name="test_login",
    category="unit",
    status="passed",
    duration_ms=150.0,
    intent="User login with valid credentials",
    linked_rules="RULE-001,SESSION-EVID-01-v1",
    linked_gaps="GAP-TEST-EVIDENCE-001"
)
```

This enables:
- Real-time test visibility in governance sessions
- Cross-session test trend analysis
- Rule compliance verification via test linkage

### Markers

```python
# Link test to rules
@pytest.mark.rules("RULE-001", "SESSION-EVID-01-v1")
def test_example():
    pass

# Link test to gaps
@pytest.mark.gaps("GAP-TEST-001")
def test_gap_fix():
    pass

# Set test intent
@pytest.mark.intent("User authentication validates credentials")
def test_auth():
    pass
```

### Manual BDD Steps (bdd_evidence fixture)

```python
def test_user_login(bdd_evidence):
    """Test user login with BDD steps."""
    bdd_evidence.given("a registered user exists", {"email": "test@example.com"})
    # ... setup code ...

    bdd_evidence.when("the user submits valid credentials")
    # ... action code ...

    bdd_evidence.then("the user receives an auth token")
    # ... assertion code ...
```

---

## Output

Evidence files are written to `evidence/tests/<run_id>/`:
- `unit/*.json` - Unit test evidence
- `integration/*.json` - Integration test evidence
- `e2e/*.json` - End-to-end test evidence
- `summary.json` - Run summary with statistics

---

## Validation

- [ ] BDD evidence enabled for certification runs
- [ ] Tests link to governance rules via markers or docstrings
- [ ] Session ID provided for governance linkage
- [ ] Summary includes rule coverage statistics

## Test Coverage

**5 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/bdd_evidence.robot` | unit |
| `tests/robot/unit/holographic_store.robot` | unit |
| `tests/robot/unit/session_test_result.robot` | unit |
| `tests/robot/unit/trace_event.robot` | unit |
| `tests/robot/unit/trace_minimizer.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TEST-EVID-01-v1 tests/robot/
```

---

*Per GAP-TEST-EVIDENCE-001: File-based test evidence with BDD structure*
*Per RD-TESTING-STRATEGY TEST-002: Evidence collection at trace level*
