# RD-ROBOT-FRAMEWORK: BDD Test Migration

**Status:** PARTIAL | **Priority:** HIGH | **Category:** Testing Strategy
**Created:** 2026-01-21 | **Updated:** 2026-01-25 | **Source:** User Request
**Migration Progress:** 64% (1419+/2217 tests)
**Reference:** https://github.com/robotframework/robotframework

---

## Executive Summary

Migrate all tests to Robot Framework using BDD approach. Apply enterprise test writing best practices for maintainability, reusability, and evidence collection.

---

## Objectives

1. **Rewrite all tests** using Robot Framework BDD syntax
2. **Apply best practices** for enterprise test architecture
3. **Enable evidence collection** per governance rules
4. **Integrate with CI/CD** for structured reporting

---

## Best Practices to Implement

### 1. Reusability
- Create shared keyword libraries
- Common setup/teardown procedures
- Reusable page objects for UI tests
- Shared API client keywords

### 2. Composability
- Layered keyword architecture (high-level → low-level)
- Business-readable test cases
- Technical implementation in resource files
- Separation of concerns (data, logic, assertions)

### 3. Parametrisation
- Data-driven tests with external data sources
- Template-based test patterns
- Variable files for environment-specific configs
- Argument defaults and overrides

### 4. Tagging
- Scope tags: `unit`, `component`, `integration`, `e2e`
- Domain tags: `rules`, `tasks`, `sessions`, `agents`
- Priority tags: `critical`, `high`, `medium`, `low`
- CI tags: `smoke`, `regression`, `nightly`

### 5. Assertions
- Clear failure messages
- Soft assertions for multiple checks
- Custom assertion keywords
- Screenshot on failure

### 6. Evidence Collection
- **Intent:** Document what test validates (linked to rules)
- **Action:** Log all API calls and UI interactions
- **Effect:** Capture actual vs expected outcomes
- Evidence files per TEST-FIX-01-v1

### 7. Selective Runner
- Tag-based execution: `robot --include critical`
- Suite-based execution
- Re-run failed tests
- Parallel execution support

### 8. Structured Reporting
- HTML reports with screenshots
- JUnit XML for CI integration
- Custom report templates
- Evidence linking to governance

---

## Task Breakdown

| ID | Task | Priority | Status | Depends On |
|----|------|----------|--------|------------|
| RF-001 | Install and configure Robot Framework | HIGH | ✅ DONE | - |
| RF-002 | Create base keyword libraries | HIGH | ✅ DONE | RF-001 |
| RF-003 | Define tagging taxonomy | HIGH | ✅ DONE | - |
| RF-004 | Migrate unit tests (88 .robot files) | MEDIUM | ✅ DONE (1279 tests) | RF-002 |
| RF-005 | Migrate chat tests (subset of pytest) | MEDIUM | DEFERRED | RF-002 |
| RF-006 | Migrate e2e tests (4 .robot files) | HIGH | ✅ DONE (35 tests) | RF-002 |
| RF-007 | Migrate remaining tests | MEDIUM | ⚠️ 64% migrated | RF-002 |
| RF-008 | Implement evidence collection | HIGH | ✅ DONE | RF-002 |
| RF-009 | Configure CI/CD integration | MEDIUM | ✅ DONE | RF-001 |
| RF-010 | Update test governance rules | HIGH | ✅ DONE | RF-003 |
| RF-011 | Create test architecture documentation | MEDIUM | ✅ DONE | All |

**Audit 2026-01-26:**
- pytest tests: 2217 total
- Robot tests: **1419+ tests (64% migrated)** - all pass
- Unit tests: 98 .robot files in `tests/robot/unit/`
- E2E tests: 4 .robot files (35 tests) in `tests/robot/e2e/`
- Libraries: 101 Python wrappers in `tests/libs/`
- **Session 2026-01-26:** +10 test files migrated (task_crud_split, quality_analyzer_split, workspace_scanner_split, health, routes_chat_split, trame_ui, mcp_server_split, embedding_pipeline_split, hybrid_router, audit_trail)
- Fixed: Browser library keyword compatibility (Page Should Contain)
- Fixed: Invalid RF syntax (Run Keywords...OR, timeout= in Click, duplicate Tags)
- Fixed: Skip If pattern to use safe dictionary access
- Fixed: Integer assertions for status codes
- **Implemented RF-003:** `tests/resources/taxonomy.resource` (tag taxonomy)
- **Implemented RF-004:** Unit test migration with Python library wrappers (88 files)
- **Implemented RF-006:** E2E test migration (governance_crud, data_integrity, platform_health, rules_api)
- **Implemented RF-008:** `tests/resources/evidence.resource` + `tests/robot/rf008_evidence.robot`
- **Implemented RF-009:** `.github/workflows/robot-tests.yml` (dry-run, API, evidence jobs)
- **Implemented RF-010:** Updated TEST-TAXON-01-v1, TEST-BDD-01-v1, TEST-FIX-01-v1 for Robot Framework
- **Implemented RF-011:** `docs/TEST-ARCHITECTURE.md` - comprehensive test guide

---

## Governance Rules Updated (RF-010)

| Rule ID | Status | Update |
|---------|--------|--------|
| TEST-TAXON-01-v1 | ✅ DONE | Added Robot tags, execution examples |
| TEST-BDD-01-v1 | ✅ DONE | Robot as preferred framework |
| TEST-FIX-01-v1 | ✅ DONE | Robot report.html as evidence |
| TEST-EVID-01-v1 | ✅ OK | Already framework-agnostic |
| TEST-COMP-01-v1 | ⏳ TODO | Add automated BDD validation |

---

## Example BDD Test Structure

```robot
*** Settings ***
Documentation    Validate session evidence logging per RULE-001
Resource         resources/api_client.robot
Resource         resources/assertions.robot
Tags             e2e    sessions    evidence    critical

*** Variables ***
${BASE_URL}      http://localhost:8082/api

*** Test Cases ***
Session Should Create Evidence File
    [Documentation]    Per SESSION-EVID-01-v1: Sessions MUST create evidence
    [Tags]    RULE-001    regression
    Given A New Session Is Started
    When Session Work Is Completed
    Then Evidence File Should Exist
    And Evidence Should Contain Session Summary

*** Keywords ***
A New Session Is Started
    [Documentation]    Start a governance session via API
    ${response}=    POST    ${BASE_URL}/sessions    {"topic": "test-session"}
    Should Be Equal As Integers    ${response.status_code}    201
    Set Suite Variable    ${SESSION_ID}    ${response.json()['session_id']}
    Log    Intent: Validate session creates evidence file
```

---

## Success Criteria

1. All existing tests migrated to Robot Framework
2. Test coverage maintained (no regression)
3. Evidence collection automated
4. CI/CD reports generated
5. Governance rules updated
6. Documentation complete

---

## Dependencies

- Robot Framework: https://robotframework.org/
- RequestsLibrary: API testing
- Browser Library: UI testing (Playwright backend)
- Pabot: Parallel execution

---

*Per WORKFLOW-RD-01-v1: R&D task with human approval gate*
