*** Settings ***
Documentation    Rule Conflict Detection + Session-Rule Linkage E2E Tests
...              Verifies EPIC-RULES-V3-P5: GET /api/rules/conflicts returns
...              structured conflict data, and session linkage counts are present
...              in rule detail API responses.
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
Conflicts Endpoint Returns 200 With Array
    [Documentation]    GET /api/rules/conflicts returns 200 and a conflicts array.
    ${resp}=    GET On Session    api    /api/rules/conflicts
    Should Be Equal As Numbers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${body}    conflicts
    Dictionary Should Contain Key    ${body}    count
    Dictionary Should Contain Key    ${body}    scope_conflicts
    Dictionary Should Contain Key    ${body}    lifecycle_conflicts
    Should Be True    ${body}[count] >= 0
    ...    Conflict count should be non-negative

Conflicts Response Contains Structured Entries
    [Documentation]    Each conflict has rule1, rule2, description fields.
    ${resp}=    GET On Session    api    /api/rules/conflicts
    ${body}=    Set Variable    ${resp.json()}
    IF    ${body}[count] > 0
        ${first}=    Get From List    ${body}[conflicts]    0
        Dictionary Should Contain Key    ${first}    rule1
        Dictionary Should Contain Key    ${first}    rule2
        Dictionary Should Contain Key    ${first}    description
    END

Scope Conflicts Detected In Real Data
    [Documentation]    With 100+ rules, scope conflicts should be detected.
    ${resp}=    GET On Session    api    /api/rules/conflicts
    ${body}=    Set Variable    ${resp.json()}
    Should Be True    ${body}[scope_conflicts] > 0
    ...    Expected at least 1 scope conflict in 100+ active rules

Enforcement Summary Still Works After P5
    [Documentation]    Regression: GET /api/rules/enforcement/summary returns 200.
    ${resp}=    GET On Session    api    /api/rules/enforcement/summary
    Should Be Equal As Numbers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${body}    mandatory
    Dictionary Should Contain Key    ${body}    total

Rule Detail Includes Session Linkage Count
    [Documentation]    GET /api/rules/{id} returns linked_sessions_count field.
    ${resp}=    GET On Session    api    /api/rules/ARCH-EBMSF-01-v1
    Should Be Equal As Numbers    ${resp.status_code}    200
    ${body}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${body}    linked_sessions_count
    Should Be True    ${body}[linked_sessions_count] >= 0
    ...    linked_sessions_count should be present and non-negative
