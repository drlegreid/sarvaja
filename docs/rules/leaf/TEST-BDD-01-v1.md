# TEST-BDD-01-v1: BDD E2E Testing Standard

**Category:** TESTING
**Priority:** HIGH
**Status:** ACTIVE
**Created:** 2026-01-14

## Semantic ID

`TEST-BDD-01-v1` - BDD E2E Testing Standard

## Directive

All E2E tests MUST use Behavior-Driven Development (BDD) paradigm with Gherkin feature files:

### Structure

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

```bash
# Run all BDD tests
pytest tests/e2e/steps/ -v

# Run by tag
pytest tests/e2e/steps/ -v -m "smoke"

# Run specific feature
pytest tests/e2e/steps/test_dashboard_steps.py -v
```

## Dependencies

- RULE-023 (TEST-COMP-01-v1): Test Before Ship
- RULE-004: Exploratory Test Automation
- GAP-TEST-001: BDD paradigm requirement

## Evidence

- Feature files: `tests/e2e/features/*.feature`
- Step definitions: `tests/e2e/steps/*.py`
- Test factories: `tests/e2e/conftest.py`

---
*Per GAP-TEST-001: BDD paradigm for E2E tests*
