# Test Architecture (RF-011)

**Status:** ACTIVE | **Updated:** 2026-01-25 | **Per:** TEST-BDD-01-v1, TEST-TAXON-01-v1

---

## Overview

Sarvaja uses a dual-framework testing strategy:
- **Robot Framework** - BDD E2E tests (preferred for new tests)
- **pytest** - Unit and integration tests

| Metric | Count |
|--------|-------|
| Robot tests | 96 |
| pytest tests | 2206 |
| Migration progress | 4.4% |

---

## Directory Structure

```
tests/
├── unit/                    # pytest unit tests
│   ├── test_*.py           # Entity-focused unit tests
│   └── ui/                 # UI component tests
├── integration/            # pytest integration tests
├── e2e/                    # E2E tests (Robot + pytest)
│   ├── *.robot             # Robot Framework suites
│   ├── features/           # Gherkin feature files
│   ├── resources/          # Robot resources for e2e
│   │   ├── common.resource # Shared keywords
│   │   ├── exploratory.resource
│   │   └── linkage.resource
│   └── robot/
│       ├── suites/         # Organized test suites
│       └── resources/      # Suite-specific resources
├── robot/                  # Robot-specific tests
│   ├── rf008_evidence.robot
│   └── resources/
│       └── api_client.robot
├── ui/                     # UI-focused Robot tests
│   ├── rules_crud.robot
│   └── resources/
│       └── governance.resource
├── resources/              # Shared test resources
│   ├── common.resource     # Common keywords
│   ├── evidence.resource   # RF-008: Evidence collection
│   └── taxonomy.resource   # RF-003: Tag taxonomy
├── evidence/               # pytest BDD evidence
└── conftest.py             # pytest configuration
```

---

## Robot Framework Architecture

### Resource Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    TEST SUITES (.robot)                      │
│  entity_crud.robot, task_lifecycle.robot, rules_crud.robot  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  DOMAIN RESOURCES                            │
│  governance.resource, linkage.resource, exploratory.resource│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SHARED RESOURCES                            │
│  common.resource, evidence.resource, taxonomy.resource       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RF LIBRARIES                              │
│  Browser, RequestsLibrary, Collections, OperatingSystem      │
└─────────────────────────────────────────────────────────────┘
```

### Key Resources

| Resource | Purpose | RF Task |
|----------|---------|---------|
| `taxonomy.resource` | Tag definitions and validation | RF-003 |
| `evidence.resource` | Evidence collection keywords | RF-008 |
| `common.resource` | Shared setup/teardown keywords | RF-002 |
| `api_client.robot` | API testing keywords | RF-002 |
| `governance.resource` | Governance UI keywords | RF-002 |

---

## Tagging Taxonomy (Per TEST-TAXON-01-v1)

### Required: Execution Scope
```robot
[Tags]    unit          # No external deps
[Tags]    integration   # Needs TypeDB/ChromaDB
[Tags]    e2e           # Full stack
[Tags]    api           # Needs REST :8082
[Tags]    browser       # Needs Playwright
[Tags]    smoke         # Quick validation
```

### Recommended: Domain
```robot
[Tags]    rules    agents    sessions    tasks    evidence    monitor
```

### Optional: Action
```robot
[Tags]    create    read    update    delete    list    validate
```

### Optional: Governance Link
```robot
[Tags]    SESSION-EVID-01-v1    TEST-GUARD-01-v1
```

---

## Running Tests

### Robot Framework

```bash
# Dry-run (syntax check)
.venv/bin/robot --dryrun --console dotted tests/

# By scope
.venv/bin/robot --include smoke tests/
.venv/bin/robot --include api --exclude slow tests/

# By domain
.venv/bin/robot --include rules tests/
.venv/bin/robot --include "rules AND create" tests/

# Specific suite
.venv/bin/robot tests/e2e/entity_crud.robot
```

### pytest

```bash
# Unit tests
.venv/bin/pytest tests/unit/ -v

# By marker
.venv/bin/pytest -m rules tests/
.venv/bin/pytest -m "unit and not slow" tests/

# With coverage
.venv/bin/pytest tests/ --cov=governance
```

---

## Evidence Collection (RF-008)

### Robot Framework

```robot
*** Settings ***
Resource    ../resources/evidence.resource
Suite Setup    Suite Evidence Setup
Suite Teardown    Suite Evidence Teardown
Test Teardown    Test Evidence Teardown    @{TEST_RULE_LINKS}

*** Test Cases ***
My Test With Evidence
    [Tags]    api    rules    SESSION-EVID-01-v1
    Set Test Variable    @{TEST_RULE_LINKS}    SESSION-EVID-01-v1
    # Test steps...
```

### pytest

```python
@pytest.mark.rules("SESSION-EVID-01-v1")
def test_with_evidence(bdd_evidence):
    bdd_evidence.given("precondition")
    bdd_evidence.when("action")
    bdd_evidence.then("assertion")
```

---

## CI/CD Integration (RF-009)

### GitHub Actions

```yaml
# .github/workflows/robot-tests.yml
jobs:
  robot-dryrun:     # Syntax validation
  robot-api-tests:  # API tests with --include api
  robot-evidence:   # RF-008 evidence tests
```

### Local CI Simulation

```bash
# Run what CI runs
.venv/bin/robot --dryrun tests/
.venv/bin/robot --include api --exclude e2e tests/robot/
.venv/bin/robot --include rf008 tests/robot/rf008_evidence.robot
```

---

## Creating New Tests

### Robot Framework Template

```robot
*** Settings ***
Documentation    Brief description. Per RULE-ID
Resource         ../resources/common.resource
Resource         ../resources/taxonomy.resource
Library          Browser    auto_closing_level=KEEP

Suite Setup      Standard Suite Setup
Suite Teardown   Standard Suite Teardown

*** Variables ***
${BASE_URL}      http://localhost:8082/api

*** Test Cases ***
Feature Should Work
    [Documentation]    Per RULE-ID: What this validates
    [Tags]    api    domain    action    RULE-ID
    Given Precondition Is Met
    When Action Is Performed
    Then Expected Outcome Occurs

*** Keywords ***
Precondition Is Met
    [Documentation]    Setup step
    Log    Setting up precondition

Action Is Performed
    [Documentation]    The action under test
    Log    Performing action

Expected Outcome Occurs
    [Documentation]    Verification
    Log    Verifying outcome
```

---

## Migration Guide (pytest → Robot)

### Before (pytest)

```python
@pytest.mark.api
@pytest.mark.rules
def test_create_rule(api_client):
    response = api_client.post("/rules", json={"title": "Test"})
    assert response.status_code == 201
```

### After (Robot)

```robot
Create Rule Should Succeed
    [Tags]    api    rules    create
    ${response}=    POST    ${BASE_URL}/rules    {"title": "Test"}
    Should Be Equal As Integers    ${response.status_code}    201
```

---

## Related Documents

- [TEST-TAXON-01-v1](rules/leaf/TEST-TAXON-01-v1.md) - Tagging taxonomy
- [TEST-BDD-01-v1](rules/leaf/TEST-BDD-01-v1.md) - BDD requirements
- [RD-ROBOT-FRAMEWORK](backlog/rd/RD-ROBOT-FRAMEWORK.md) - Migration epic

---

*Per RF-011: Test architecture documentation*
