# Skill: Test Automation

**ID:** SKILL-QA-AUTOMATE-001
**Tags:** qa, automation, testing, ci
**Requires:** playwright, rest-api, Bash, Write

## When to Use
- Converting exploratory test to repeatable test
- Adding regression coverage
- Creating CI pipeline tests
- Building smoke test suites

## Procedure
1. Review exploratory test findings
2. Identify automation candidates (stable, repeatable)
3. Choose appropriate framework:
   - **Playwright** → UI/E2E tests
   - **Pytest** → API/unit tests
   - **Robot** → Acceptance tests
4. Write test with clear assertions
5. Add to appropriate test suite
6. Verify test passes/fails correctly

## Framework Selection

| Test Type | Framework | Location |
|-----------|-----------|----------|
| UI E2E | Playwright (MCP) | tests/e2e/*.py |
| API | Pytest + requests | tests/test_*.py |
| Acceptance | Robot Framework | tests/e2e/*.robot |
| Unit | Pytest | tests/test_*.py |

## Test Pattern Templates

### Playwright UI Test
```python
async def test_rules_view_loads():
    """Verify rules view displays rule count."""
    await page.goto("http://localhost:8081")
    await page.click('[data-testid="nav-rules"]')
    count = await page.text_content('[data-testid="rules-count"]')
    assert "37 rules" in count
```

### Pytest API Test
```python
def test_health_endpoint():
    """Verify API health check."""
    response = requests.get("http://localhost:8082/api/health")
    assert response.status_code == 200
    assert response.json()["typedb_connected"] == True
```

### Robot Framework Test
```robot
*** Test Cases ***
Dashboard Shows Rules Count
    [Tags]    smoke    ui
    Navigate To Dashboard
    Click Navigation Item    Rules
    Page Should Contain    37 rules loaded
```

## Evidence Output
- Test file in appropriate directory
- Test execution log
- Coverage report update

## Automation Criteria

Tests are good automation candidates when:
- ✅ Steps are deterministic (same input → same output)
- ✅ No external dependencies (stable test data)
- ✅ Fast execution (<30 seconds)
- ✅ Clear pass/fail criteria

Tests should remain manual when:
- ❌ Requires visual judgment
- ❌ Exploratory in nature
- ❌ Depends on real-time external data
- ❌ One-time validation
