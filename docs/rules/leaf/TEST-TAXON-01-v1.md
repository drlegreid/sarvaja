# TEST-TAXON-01-v1: Test Taxonomy & Marker Strategy

**Rule ID:** TEST-TAXON-01-v1
**Category:** testing
**Priority:** HIGH
**Status:** ACTIVE
**Created:** 2026-01-21
**Updated:** 2026-01-28
**Linked:** TEST-EXEC-01-v1, TEST-BDD-01-v1, RF-003

---

## Directive

All tests MUST use markers/tags following the taxonomy below to enable selective execution by domain, entity, action, or concern. Tests without appropriate markers/tags are considered incomplete.

**Applies to:**
- **pytest**: Use `@pytest.mark.<tag>` decorators
- **Robot Framework**: Use `[Tags]    <tag1>    <tag2>` setting

---

## Taxonomy Dimensions

### 1. Execution Scope (REQUIRED)
At least ONE scope marker/tag is required:

| Tag | pytest | Robot Framework | Description |
|-----|--------|-----------------|-------------|
| `unit` | `@pytest.mark.unit` | `[Tags]    unit` | No external dependencies |
| `integration` | `@pytest.mark.integration` | `[Tags]    integration` | Needs TypeDB/ChromaDB |
| `e2e` | `@pytest.mark.e2e` | `[Tags]    e2e` | Full services required |
| `api` | `@pytest.mark.api` | `[Tags]    api` | Needs REST server :8082 |
| `browser` | `@pytest.mark.browser` | `[Tags]    browser` | Needs Playwright |
| `smoke` | `@pytest.mark.smoke` | `[Tags]    smoke` | Quick validation |

### 2. Domain Markers (Recommended)
What system area is being tested:
- `rules`, `agents`, `sessions`, `tasks`, `gaps`, `evidence`
- `ui`, `mcp`, `hooks`, `chroma`, `typedb`, `monitor`

### 3. Entity Markers (Optional)
What specific entity type:
- `rule`, `agent`, `session`, `task`, `proposal`, `trust`, `decision`, `gap`

### 4. Action Markers (Optional)
What operation is being tested:
- `create`, `read`, `read_detail`, `update`, `delete`, `list`
- `validate`, `migrate`, `sync`

### 5. Concern Markers (CRUCSS, Optional)
What quality attribute (with CRUCSS pillars):
- `capability` (P9.8), `reliability` (P9.5), `usability` (P8.9)
- `security` (P9.0), `scalability` (P8.5), `supportability` (P8.3)
- `performance`, `accessibility`, `a11y`

### 6. CI/CD Markers (Optional)
When should this test run:
- `critical` - Every commit
- `regression` - Daily
- `nightly` - Overnight
- `manual` - On-demand only
- `skip` - Temporarily disabled

### 7. Governance Linking (Recommended for E2E)
Link tests to rules for evidence collection:
- pytest: `@pytest.mark.SESSION_EVID_01_v1`
- Robot: `[Tags]    SESSION-EVID-01-v1`

---

## Usage Examples

### pytest Examples

```python
# Single rule creation test
@pytest.mark.unit
@pytest.mark.rules
@pytest.mark.create
def test_create_rule_success():
    ...

# Agent trust performance benchmark
@pytest.mark.benchmark
@pytest.mark.agents
@pytest.mark.trust
@pytest.mark.performance
def test_trust_calculation_performance():
    ...
```

### Robot Framework Examples

```robot
*** Test Cases ***
Rule Creation Should Succeed
    [Documentation]    Per TEST-TAXON-01-v1: Proper tagging example
    [Tags]    api    rules    create    critical    SESSION-EVID-01-v1
    ${response}=    POST    ${BASE_URL}/rules    {"title": "Test"}
    Should Be Equal As Integers    ${response.status_code}    201

Agent Trust Score Is Calculated
    [Tags]    integration    agents    trust    capability    P9.8
    Given Agent Is Registered    agent-001
    When Trust Is Recalculated
    Then Trust Score Should Be Valid
```

---

## Running Tests by Taxonomy

### pytest

```bash
pytest -m rules                      # Run all rule tests
pytest -m "rules and create"         # Rule creation only
pytest -m "agents and performance"   # Agent performance tests
pytest -m "unit and not slow"        # Unit tests excluding slow
```

### Robot Framework

```bash
robot --include rules tests/         # Run all rule tests
robot --include "rules AND create" tests/  # Rule creation only
robot --include api --exclude slow tests/  # API tests excluding slow
robot --include critical tests/      # Critical tests only
robot --dryrun tests/                # Syntax validation only
```

---

## Bidirectional Traceability (Dimension 8)

Tests and rules form a **two-way traceability chain**:

### Direction 1: Tests → Rules (via tags)
Each Robot test file includes governance rule IDs in `Force Tags`:
```robot
Force Tags    unit    rules    high    GOV-RULE-01-v1
```
This enables: `robot --include GOV-RULE-01-v1 tests/robot/` to run all tests for that rule.

### Direction 2: Rules → Tests (via doc sections)
Each leaf rule document in `docs/rules/leaf/` includes a `## Test Coverage` section listing all robot test files that validate it, with file paths and execution commands.

### Maintenance
- When a **new test** references a rule via tags, update the rule's `## Test Coverage` section
- When a **rule is created**, add it to relevant test files' `Force Tags` and create the `## Test Coverage` section
- **Reverse mapping script**: `/tmp/reverse_mapping.py` generates the full rule→test mapping
- **Current coverage**: 38 rules → 138 test file references (42 unique governance rules across 139 robot files)

### Queryable Traceability
```bash
# Find tests for a rule (Direction 1)
robot --include SESSION-EVID-01-v1 tests/robot/

# Find rules for a test (Direction 2 - grep Force Tags)
grep -l "SESSION-EVID-01-v1" tests/robot/**/*.robot
```

---

## Compliance

- **NEW tests** MUST include at least ONE scope marker/tag
- **NEW tests** SHOULD include governance rule IDs in `Force Tags` when applicable
- **EXISTING tests** SHOULD be retroactively tagged in maintenance cycles
- **CI/CD** MAY split test runs by marker/tag groups for faster feedback
- **Coverage reports** SHOULD group by domain markers/tags
- **Robot tests** MUST import `taxonomy.resource` for validation keywords
- **Rule docs** MUST include `## Test Coverage` section with robot file references (bidirectional)

---

## Evidence

- `pytest.ini` - pytest marker definitions
- `tests/resources/taxonomy.resource` - Robot Framework tag definitions (RF-003)
- `.github/workflows/robot-tests.yml` - CI/CD using Robot tags (RF-009)
- `tests/robot/ROBOT-TAXONOMY.md` - Compliance status and queryable examples
- `docs/rules/leaf/*.md` - 38 rule docs with `## Test Coverage` sections (bidirectional)
- Test files with marker/tag annotations (139 robot files, 42 unique rule refs)

---

## Related

- RF-003: Robot Framework tagging taxonomy implementation
- RF-009: CI/CD integration with tag-based execution
- TEST-BDD-01-v1: BDD syntax requirements

## Test Coverage

**2 robot test file(s)** validate this rule:

| File | Scope |
|------|-------|
| `tests/robot/unit/gap_parser.robot` | unit |
| `tests/robot/unit/rules_validation.robot` | unit |

```bash
# Run all tests validating this rule
robot --include TEST-TAXON-01-v1 tests/robot/
```

---

*Per META-TAXON-01-v1: Taxonomy-based organization*
