# TEST-BDD-01-v1: BDD E2E Testing Standard

**Category:** `testing`
**Priority:** HIGH
**Type:** OPERATIONAL
**Status:** ACTIVE
**Created:** 2026-01-14
**Updated:** 2026-01-25

## Semantic ID

`TEST-BDD-01-v1` - BDD E2E Testing Standard

## Directive

All E2E tests MUST use Behavior-Driven Development (BDD) paradigm.

**Supported Frameworks:**
- **Robot Framework** (PREFERRED for new tests) - Native Given/When/Then
- **pytest-bdd** - Python with Gherkin feature files

### Structure (Robot Framework — Primary)

```
tests/e2e/robot/
├── suites/             # .robot test suites by domain
│   ├── dashboard_navigation.robot
│   ├── rules_view.robot
│   ├── tasks_view.robot
│   ├── sessions_view.robot
│   ├── trust_agents_view.robot
│   ├── infra_view.robot
│   └── smoke.robot
├── resources/          # Shared .resource files
│   ├── common.resource     # Setup/teardown keywords
│   ├── selectors.resource  # Centralized CSS selectors
│   └── api.resource        # REST API test keywords
└── libraries/          # Python keyword libraries (SRP)
    ├── actions.py      # Click, fill, scroll, Fibonacci backoff
    ├── navigation.py   # Tab navigation, page verification
    └── overlay.py      # Vuetify overlay management
```

Per TEST-E2E-FRAMEWORK-01-v1: Each library follows SRP, max 300 lines.

### Structure (pytest-bdd — Legacy)

```
tests/e2e/
├── features/           # Gherkin .feature files
│   ├── dashboard.feature
│   └── crud_operations.feature
├── steps/              # Step definitions
│   ├── conftest.py     # Shared fixtures
│   └── test_*.py       # Step implementations
└── conftest.py         # E2E configuration
```

### Feature File Format

```gherkin
@e2e @<domain>
Feature: <Feature Name>
  As a <role>
  I want to <action>
  So that <benefit>

  Background:
    Given <common setup>

  @<tag>
  Scenario: <Scenario Name>
    When <action>
    Then <assertion>
```

### Step Definition Pattern

```python
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios
scenarios("../features/<feature>.feature")

@given("the dashboard is running")
def dashboard_running():
    pass

@when(parsers.parse('I click on "{tab}" navigation'))
def click_tab(page: Page, tab: str):
    page.click(f"[data-testid='nav-{tab.lower()}']")

@then(parsers.parse('I should see "{text}"'))
def should_see_text(page: Page, text: str):
    expect(page.locator(f"text={text}").first).to_be_visible()
```

### Required Tags

- `@e2e` - All E2E scenarios
- `@smoke` - Critical path tests
- `@crud` - Create/Read/Update/Delete tests
- `@<domain>` - Domain-specific (rules, tasks, agents, etc.)

### Test Execution

**Robot Framework:**
```bash
# Run all BDD tests (compact output)
robot --console dotted tests/

# Run by tag
robot --include smoke tests/

# Run specific suite
robot tests/e2e/entity_crud.robot
```

**pytest-bdd:**
```bash
pytest tests/e2e/steps/ -v
pytest tests/e2e/steps/ -v -m "smoke"
```

## BDD Beyond E2E (GAP-TEST-EVIDENCE-003)

BDD principles apply at ALL test levels, not just E2E:

| Level | BDD Approach |
|-------|--------------|
| **Unit** | Programmatic Given/When/Then via `bdd_evidence` fixture |
| **Integration** | Contract-style Given (setup) / When (call) / Then (verify) |
| **E2E** | Full Gherkin feature files with Playwright |

### Unit/Integration BDD Pattern

```python
def test_rule_creation(bdd_evidence):
    """Test creating governance rule. Per RULE-001."""
    bdd_evidence.given("TypeDB is connected", {"host": "localhost"})
    # setup code...

    bdd_evidence.when("I create a new rule")
    result = client.create_rule(rule_id="TEST-001", name="Test Rule")

    bdd_evidence.then("the rule exists in TypeDB")
    assert client.get_rule_by_id("TEST-001") is not None
```

This produces structured evidence per TEST-EVID-01-v1 without requiring Gherkin files.

---

## Dependencies

- TEST-COMP-02-v1: Test Before Ship
- TEST-EVID-01-v1: BDD Evidence Collection
- TEST-TDD-01-v1: Test-Driven Development
- GAP-TEST-001: BDD paradigm requirement

## Evidence

- Robot Framework suites: `tests/e2e/robot/suites/*.robot`
- RF keyword libraries: `tests/e2e/robot/libraries/*.py`
- RF resource files: `tests/e2e/robot/resources/*.resource`
- Legacy feature files: `tests/e2e/features/*.feature`
- Programmatic BDD: `tests/evidence/collector.py`

---
*Per GAP-TEST-001: BDD paradigm for E2E tests*
*Per GAP-TEST-EVIDENCE-003: BDD at all test levels*

## Test Coverage

**2 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/e2e/dashboard_browser.robot` | e2e |
| `tests/robot/unit/kanren_rag.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TEST-BDD-01-v1 tests/robot/
```
