*** Settings ***
Documentation    Rule Applicability Enforcement Summary E2E Tests
...              Verifies EPIC-RULES-V3-P4: GET /api/rules/enforcement/summary
...              returns real counts per applicability level and lists
...              unimplemented MANDATORY rules.
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
# ENFORCEMENT SUMMARY — EPIC-RULES-V3-P4
# =============================================================================

Enforcement Summary Returns 200
    [Documentation]    GET /api/rules/enforcement/summary must return 200.
    [Tags]    enforcement    critical    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/enforcement/summary
    Should Be Equal As Integers    ${response.status_code}    200

Enforcement Summary Contains Applicability Counts
    [Documentation]    Response must include mandatory, recommended, forbidden,
    ...                conditional, and total counts.
    [Tags]    enforcement    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/enforcement/summary
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${body}    mandatory
    Dictionary Should Contain Key    ${body}    recommended
    Dictionary Should Contain Key    ${body}    forbidden
    Dictionary Should Contain Key    ${body}    conditional
    Dictionary Should Contain Key    ${body}    total
    # Total should be sum of parts
    ${sum}=    Evaluate    ${body}[mandatory] + ${body}[recommended] + ${body}[forbidden] + ${body}[conditional] + ${body}[unspecified]
    Should Be Equal As Integers    ${sum}    ${body}[total]

Enforcement Summary Has Non-Zero Mandatory Count
    [Documentation]    At least 1 MANDATORY rule should exist in TypeDB.
    [Tags]    enforcement    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/enforcement/summary
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Should Be True    ${body}[mandatory] > 0
    ...    No MANDATORY rules found — applicability data may be missing

Enforcement Summary Lists Unimplemented Mandatory
    [Documentation]    Response must include unimplemented_mandatory list.
    [Tags]    enforcement    high    epic-rules-v3
    ${response}=    GET On Session    api    /api/rules/enforcement/summary
    Should Be Equal As Integers    ${response.status_code}    200
    ${body}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${body}    unimplemented_mandatory
    ${unimpl}=    Get From Dictionary    ${body}    unimplemented_mandatory
    # Each entry should have rule_id and name
    IF    len($unimpl) > 0
        ${first}=    Get From List    ${unimpl}    0
        Dictionary Should Contain Key    ${first}    rule_id
        Dictionary Should Contain Key    ${first}    name
    END
