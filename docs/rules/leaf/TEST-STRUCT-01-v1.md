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

## 4. Framework Separation (CRITICAL - No Cross-Framework Duplication)

### Rule
Each test layer MUST use ONE framework. pytest and Robot Framework MUST NOT duplicate the same test logic.

### Framework Responsibilities

| Layer | Framework | Rationale |
|-------|-----------|-----------|
| **Unit tests** | pytest | Native Python, fast, fixtures |
| **E2E / Integration** | Robot Framework | Structured reporting, tags, BDD |
| **Browser tests** | Robot Framework + Browser | Keyword-driven, report-friendly |
| **API validation** | Robot Framework | Data-driven tables, tagging |

### Anti-Patterns (PROHIBITED)

```
# BAD: Triple-layer duplication
tests/test_vector_store.py           # pytest test
tests/libs/VectorStoreLibrary.py     # wrapper library
tests/robot/unit/vector_store.robot  # Robot test calling wrapper

# GOOD: One framework per layer
tests/unit/test_vector_store.py      # pytest unit test (ONLY)
tests/robot/e2e/vector_store.robot   # Robot E2E test (different scope)
```

### Migration Path
1. Unit tests in `tests/` root that have Robot equivalents → keep pytest, remove Robot wrapper
2. Robot `tests/libs/*.py` that wrap pytest logic → remove after migration
3. Robot unit tests (`tests/robot/unit/`) → graduate to E2E or remove

---

## 5. No Low-Value Structural Tests

### Rule
Tests that only verify module/class/method existence MUST be removed. Import failures will surface in behavioral tests naturally.

### Prohibited Patterns
```python
# BAD: Zero regression value
def test_module_exists():
    assert Path("governance/client.py").exists()

def test_class_exists():
    from governance.client import GovernanceClient
    assert GovernanceClient is not None

def test_has_required_methods():
    assert hasattr(GovernanceClient, "get_all_rules")
```

### Acceptable Alternative
```python
# GOOD: Test the behavior, not the structure
def test_get_all_rules_returns_list():
    client = GovernanceClient()
    rules = client.get_all_rules()
    assert isinstance(rules, list)
```

---

## Compliance

- **NEW tests** MUST follow DRY, SRP, OOP before merge
- **NEW tests** MUST NOT duplicate logic across pytest and Robot Framework
- **EXISTING tests** SHOULD be refactored during maintenance cycles
- **Code review** MUST check for repeated logic (>3 occurrences)
- **Library files** MUST use class-based structure with `ROBOT_LIBRARY_SCOPE`
- **Each test** MUST validate a single behavior
- **`test_*_module_exists`** patterns MUST be removed in next maintenance cycle

---

## Compliance Audit (2026-02-01)

| Check | Status | Detail |
|-------|--------|--------|
| DRY: No duplicate logic | **PASS** | 75 Robot unit wrappers removed (Phase 2) |
| DRY: Shared keywords used | **PASS** | 1,184 inline skip blocks eliminated (Phase 2) |
| SRP: One behavior per test | **PASS** | 56 structural tests removed from 32 files (Phase 1) |
| OOP: Class-based libraries | **PASS** | 3 E2E libraries retained in `tests/robot/e2e/libs/` |
| Framework separation | **PASS** | Unit=pytest only, E2E=Robot only |
| Marker coverage (pytest) | **PASS** | 82.1% auto-marked (extended conftest hook) |
| Tag coverage (Robot) | PASS | ~100% tagged |

**Remediation completed (2026-02-01):**
1. ~~Remove 75 Robot unit wrappers~~ → DONE: 134 Robot unit files + 191 wrapper libs removed
2. ~~Remove ~200 structural tests~~ → DONE: 56 low-value tests removed from 32 files
3. ~~Consolidate 1,184 inline skip blocks~~ → DONE: eliminated with Robot unit removal
4. ~~Mark unmarked pytest tests~~ → DONE: auto-marking extended (82.1% coverage)

**Post-cleanup metrics:**
- Pytest: 3,015 tests collected (unit: 1,197, E2E: 67, root: ~1,751)
- Robot Framework: 4 E2E suites with 3 shared libraries
- Files removed: 325 (134 Robot unit + 191 wrapper libs)

---

## Evidence

- Test files following these patterns
- Resource files with reusable keywords
- Library classes with proper scope settings
- `conftest.py` with shared fixtures
- Compliance audit: 2026-02-01 (this section)
- Phase 1: 56 structural tests removed from 32 files
- Phase 2: 325 files removed (Robot unit + wrapper libs)

---

## Related

- TEST-TAXON-01-v1: Taxonomy and tagging (complements structure)
- ARCH-EBMSF-01-v1: Test evidence structure (WHY/WHAT/PROVE)
- TEST-BDD-01-v1: BDD syntax (Given/When/Then)
- DOC-SIZE-01-v1: File size limits (max 300 lines)
- TEST-EXEC-01-v1: Split test execution (framework separation)

---

*Per META-TAXON-01-v1: Taxonomy-based organization*
