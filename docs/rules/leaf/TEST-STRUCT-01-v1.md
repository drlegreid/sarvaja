# TEST-STRUCT-01-v1: Test Code Quality - DRY, SRP & OOP

**Rule ID:** TEST-STRUCT-01-v1
**Category:** testing
**Priority:** HIGH
**Status:** ACTIVE
**Created:** 2026-01-28
**Linked:** TEST-TAXON-01-v1, ARCH-EBMSF-01-v1, TEST-BDD-01-v1

---

## Directive

All test code MUST follow DRY (Don't Repeat Yourself), SRP (Single Responsibility Principle), and OOP (Object-Oriented Programming) principles to ensure maintainability, readability, and reuse.

**Applies to:**
- **pytest**: Test modules, fixtures, conftest.py
- **Robot Framework**: Test suites, resource files, Python libraries

---

## 1. DRY - Don't Repeat Yourself

### Rule
Repeated test logic MUST be extracted into reusable components.

### pytest
```python
# BAD: Repeated setup in every test
def test_create_rule():
    client = GovernanceClient("http://localhost:8082")
    response = client.post("/api/rules", {"title": "Rule A"})
    assert response.status_code == 201

def test_update_rule():
    client = GovernanceClient("http://localhost:8082")  # REPEATED
    response = client.post("/api/rules", {"title": "Rule B"})  # REPEATED
    ...

# GOOD: Extracted to fixture
@pytest.fixture
def governance_client():
    return GovernanceClient("http://localhost:8082")

@pytest.fixture
def sample_rule(governance_client):
    response = governance_client.post("/api/rules", {"title": "Test Rule"})
    return response.json()

def test_create_rule(governance_client):
    response = governance_client.post("/api/rules", {"title": "Rule A"})
    assert response.status_code == 201

def test_update_rule(governance_client, sample_rule):
    response = governance_client.put(f"/api/rules/{sample_rule['id']}", {...})
    assert response.status_code == 200
```

### Robot Framework
```robot
# BAD: Repeated keywords inline
Create Rule A
    ${response}=    POST    ${BASE_URL}/api/rules    {"title": "A"}
    Should Be Equal As Integers    ${response.status_code}    201

Create Rule B
    ${response}=    POST    ${BASE_URL}/api/rules    {"title": "B"}
    Should Be Equal As Integers    ${response.status_code}    201

# GOOD: Reusable keyword in resource file
*** Keywords ***
Create Rule
    [Arguments]    ${title}    ${expected_status}=201
    ${payload}=    Create Dictionary    title=${title}
    ${response}=    POST    ${BASE_URL}/api/rules    json=${payload}
    Should Be Equal As Integers    ${response.status_code}    ${expected_status}
    RETURN    ${response.json()}
```

### Thresholds
- **Max 3 repetitions** before extraction is required
- Shared keywords belong in `*.resource` files, not duplicated across suites
- Shared Python logic belongs in `conftest.py` or library classes

---

## 2. SRP - Single Responsibility Principle

### Rule
Each test MUST validate ONE behavior. Each library/resource file MUST serve ONE domain.

### Test Granularity
```python
# BAD: Testing multiple behaviors in one test
def test_rule_lifecycle():
    rule = create_rule("Test")           # CREATE
    assert rule["title"] == "Test"
    update_rule(rule["id"], "Updated")    # UPDATE
    assert get_rule(rule["id"])["title"] == "Updated"
    delete_rule(rule["id"])               # DELETE
    assert get_rule(rule["id"]) is None

# GOOD: One behavior per test
def test_create_rule(governance_client):
    response = governance_client.post("/api/rules", {"title": "Test"})
    assert response.status_code == 201

def test_update_rule(governance_client, sample_rule):
    response = governance_client.put(f"/api/rules/{sample_rule['id']}", {"title": "Updated"})
    assert response.status_code == 200

def test_delete_rule(governance_client, sample_rule):
    response = governance_client.delete(f"/api/rules/{sample_rule['id']}")
    assert response.status_code == 200
```

### File Organization
| Wrong | Right |
|-------|-------|
| `test_everything.py` (500 lines) | `test_rules_crud.py`, `test_rules_validation.py` |
| `AllTestsLibrary.py` | `RulesCrudLibrary.py`, `RulesValidationLibrary.py` |
| One resource for all domains | `rules.resource`, `sessions.resource`, `tasks.resource` |

### Thresholds
- **Max 1 assertion topic per test** (multiple asserts on same result OK)
- **Max 300 lines per test file** (per DOC-SIZE-01-v1)
- **Max 20 keywords per resource file**

---

## 3. OOP - Object-Oriented Principles

### Rule
Test libraries MUST use class-based organization with proper encapsulation.

### Robot Framework Libraries
```python
# BAD: Flat functions, no encapsulation
def create_rule(title):
    import requests
    return requests.post("http://localhost:8082/api/rules", json={"title": title})

def get_rule(rule_id):
    import requests
    return requests.get(f"http://localhost:8082/api/rules/{rule_id}")

# GOOD: Class with shared state and proper scope
class RulesCrudLibrary:
    """Library for testing rules CRUD operations."""

    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self, base_url="http://localhost:8082"):
        self._base_url = base_url
        self._session = None

    @keyword("Create Rule")
    def create_rule(self, title, **kwargs):
        """Create a rule via API. Returns response dict."""
        ...

    @keyword("Get Rule By ID")
    def get_rule(self, rule_id):
        """Retrieve a rule by ID. Returns rule dict."""
        ...
```

### pytest Fixtures as Dependency Injection
```python
# GOOD: Fixtures provide clean dependency injection
@pytest.fixture(scope="session")
def api_client():
    """Shared API client for the test session."""
    client = GovernanceAPIClient(base_url=os.environ.get("API_URL", "http://localhost:8082"))
    yield client
    client.close()

@pytest.fixture
def rule_factory(api_client):
    """Factory for creating test rules with cleanup."""
    created = []
    def _create(**kwargs):
        rule = api_client.create_rule(**kwargs)
        created.append(rule["id"])
        return rule
    yield _create
    for rule_id in created:
        api_client.delete_rule(rule_id)
```

### Principles
- **Encapsulation**: Internal state (URLs, sessions, auth) hidden in class `__init__`
- **Inheritance**: Base library classes for shared behavior (`BaseAPILibrary`)
- **Composition**: Libraries compose smaller utilities, not monolith methods
- **ROBOT_LIBRARY_SCOPE**: Use `SUITE` for stateful, `GLOBAL` for stateless

---

## Compliance

- **NEW tests** MUST follow DRY, SRP, OOP before merge
- **EXISTING tests** SHOULD be refactored during maintenance cycles
- **Code review** MUST check for repeated logic (>3 occurrences)
- **Library files** MUST use class-based structure with `ROBOT_LIBRARY_SCOPE`
- **Each test** MUST validate a single behavior

---

## Evidence

- Test files following these patterns
- Resource files with reusable keywords
- Library classes with proper scope settings
- `conftest.py` with shared fixtures

---

## Related

- TEST-TAXON-01-v1: Taxonomy and tagging (complements structure)
- ARCH-EBMSF-01-v1: Test evidence structure (WHY/WHAT/PROVE)
- TEST-BDD-01-v1: BDD syntax (Given/When/Then)
- DOC-SIZE-01-v1: File size limits (max 300 lines)

---

*Per META-TAXON-01-v1: Taxonomy-based organization*
