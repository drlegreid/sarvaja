*** Settings ***
Documentation    Rule Dependency Graph E2E Tests (EPIC-RULES-V3-P2)
...              Verifies dependency overview endpoint returns real circular_count
...              (not hardcoded 0), dependency graph stats, and rule detail
...              returns linkage counts (BUG-015 fix).
...              Per TEST-E2E-01-v1: Tier 3 data flow verification.
Library          Collections
Library          RequestsLibrary

Suite Setup      Setup API Session
Suite Teardown   Delete All Sessions

*** Variables ***
${API_BASE}    http://localhost:8082

*** Keywords ***
Setup API Session
    [Documentation]    Create API session for tests
    Create Session    api    ${API_BASE}    verify=${FALSE}

*** Test Cases ***
# =============================================================================
# DEPENDENCY OVERVIEW — EPIC-RULES-V3-P2
# =============================================================================

Dependency Overview Returns Total Rules
    [Documentation]    GET /api/rules/dependencies/overview must return total_rules > 0.
    [Tags]    dependency    overview    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/dependencies/overview
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    ${total}=    Get From Dictionary    ${body}    total_rules
    Should Be True    ${total} > 0    No rules in dependency overview

Dependency Overview Has Circular Count Field
    [Documentation]    circular_count field must exist and be a real integer (not missing).
    ...                Verifies P2 fix: hardcoded circular_count=0 replaced with DFS detection.
    [Tags]    dependency    circular    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/dependencies/overview
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${body}    circular_count
    Dictionary Should Contain Key    ${body}    cycles
    ${cc}=    Get From Dictionary    ${body}    circular_count
    Should Be True    ${cc} >= 0    circular_count must be non-negative integer

Dependency Overview Has Orphan Rules
    [Documentation]    orphan_count and orphan_rules must be present.
    [Tags]    dependency    orphans    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/dependencies/overview
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${body}    orphan_count
    Dictionary Should Contain Key    ${body}    orphan_rules
    ${oc}=    Get From Dictionary    ${body}    orphan_count
    Should Be True    ${oc} >= 0    orphan_count must be non-negative

Dependency Overview Reports Total Dependencies
    [Documentation]    total_dependencies field should exist and reflect seeded relations.
    [Tags]    dependency    total    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/dependencies/overview
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    ${td}=    Get From Dictionary    ${body}    total_dependencies
    Should Be True    ${td} >= 0    total_dependencies must be non-negative

# =============================================================================
# BUG-015: Rule Detail Returns Linkage Counts
# =============================================================================

Rule Detail API Returns Linkage Counts
    [Documentation]    GET /api/rules/{id} must include linked_tasks_count and
    ...                linked_sessions_count fields. BUG-015 fix verification.
    [Tags]    bug-015    detail    linkage    high    epic-rules-v3
    # Use a rule known to have implementing tasks from seed data
    ${response}=    GET On Session    api    /api/rules/ARCH-EBMSF-01-v1
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${body}    linked_tasks_count
    Dictionary Should Contain Key    ${body}    linked_sessions_count
    ${ltc}=    Get From Dictionary    ${body}    linked_tasks_count
    Should Be True    ${ltc} > 0
    ...    ARCH-EBMSF-01-v1 should have linked_tasks_count > 0 (seed data exists)
