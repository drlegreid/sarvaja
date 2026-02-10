# TEST-SPEC-01-v1: 3-Tier Validation Specifications

**Category:** `testing` | **Priority:** HIGH | **Status:** ACTIVE | **Type:** OPERATIONAL

> **Tags:** `testing`, `specification`, `gherkin`, `robot-framework`, `mcp`, `3-tier`

---

## Directive

Orchestrator validation MUST produce **3-tier Gherkin-style specifications** for every validated task. These specs serve as the contract between dynamic MCP-driven testing and static Robot Framework regression tests.

---

## Tier Definitions

| Tier | Name | Purpose | Audience | Detail |
|------|------|---------|----------|--------|
| 1 | Business Intent | What/Why | Stakeholders | Feature + user story (~50 tokens) |
| 2 | Technical Intent | What/How | Developers | Scenario + Given/When/Then (~200 tokens) |
| 3 | Low-Level Details | Exact contract | QA/Automation | HTTP requests, UI interactions (~500 tokens) |

---

## Tier 1: Business Intent

```gherkin
Feature: Session lifecycle management [GAP-SESSION-001]
  As a governance administrator
  I want to call /api/sessions
  So that session lifecycle is verified
```

**Required elements:** Feature name, As-a, I-want, So-that, task_id reference.

---

## Tier 2: Technical Intent

```gherkin
  Scenario: GAP-SESSION-001 - Fix session evidence capture
    Given the governance API is running
    When I send GET to /api/sessions
    Then the response status should indicate success
    And the response body should contain expected data
```

**Required elements:** Scenario, Given/When/Then, endpoint, method, validation/retry/cycle context.

---

## Tier 3: Low-Level Details

```
  # Low-level API contract for GAP-SESSION-001
  # MCP: rest-api
  Request: POST /api/sessions
  Header: Content-Type: application/json
  Body: {"topic": "test-session", "agent_id": "code-agent"}
  Expected: status 201
  Validate: response body is JSON
```

**Required elements:** HTTP method, endpoint, headers (for POST), body (if applicable), expected status, MCP tool reference.

---

## MCP Integration

| Spec Type | MCP Tool | Dynamic Execution |
|-----------|----------|-------------------|
| API | `rest-api` (dkmaker-mcp-rest-api) | `test_request` tool |
| UI | `playwright` (@playwright/mcp) | `browser_navigate`, `browser_snapshot` |

Specs include `mcp_tool` metadata indicating which MCP server executes them dynamically.

---

## Robot Framework Export

Specs export to BDD-style Robot Framework test cases:

```robot
*** Settings ***
Documentation    Feature: Session CRUD [GAP-TEST-001]
Library          RequestsLibrary
Test Tags        GAP-TEST-001    spec-tier    TEST-SPEC-01-v1

*** Test Cases ***

GAP-TEST-001 Validation
    [Documentation]    Scenario: GAP-TEST-001 - Session CRUD
    [Tags]    GAP-TEST-001    e2e
    Given API Is Running
    When Send GET Request    /api/sessions
    Then Response Status Should Be Success
```

---

## Generation Points

| When | Function | Output |
|------|----------|--------|
| Orchestrator validate_node | `generate_specs_from_validation()` | Per-task specs |
| Batch backlog | `generate_batch_specs()` | All backlog specs |
| Single endpoint | `generate_spec()` | One spec |
| RF export | `export_to_robot()` | .robot file content |

---

## Safety Constraints

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Max specs per task | 10 | Prevent spec explosion |
| Tier 3 body truncation | 500 chars | Keep specs readable |
| Default method | GET | Safe default for exploration |
| Default status | 200 | Optimistic validation |

---

## Implementation Reference

- **Spec Generator**: `governance/workflows/orchestrator/spec_tiers.py`
- **Unit Tests**: `tests/unit/test_spec_tiers.py` (18 tests)
- **Integration**: `validate_node` in `governance/workflows/orchestrator/nodes.py`

---

## Related

- WORKFLOW-ORCH-01-v1: Orchestrator workflow (generates specs during validation)
- TEST-COMP-01-v1: LLM-driven E2E test generation (exploration → generation)
- TEST-COMP-02-v1: Test before ship (specs enforce this)
- TEST-BDD-01-v1: Robot Framework BDD pattern (export target)

---

*Per META-TAXON-01-v1: Semantic rule naming*
*Created: 2026-02-11 — TDD-first 3-tier validation specification system*
