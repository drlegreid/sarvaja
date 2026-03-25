*** Settings ***
Documentation    Rule Heuristic Checks E2E Tests (EPIC-RULES-V3-P3)
...              Verifies H-RULE-002, H-RULE-005, H-RULE-006 are registered
...              in the heuristic check registry and execute via CVP sweep API.
...              Per TEST-E2E-01-v1: Tier 3 data flow verification.
Library          Collections
Library          RequestsLibrary
Library          BuiltIn

Suite Setup      Setup API Session
Suite Teardown   Delete All Sessions

*** Variables ***
${API_BASE}       http://localhost:8082
${HEUR_URL}       /api/tests/heuristic/run
&{RULE_PARAMS}    domain=RULE

*** Keywords ***
Setup API Session
    [Documentation]    Create API session for tests
    Create Session    api    ${API_BASE}    verify=${FALSE}

Trigger Rule Heuristic Run
    [Documentation]    POST heuristic run for RULE domain and return run_id
    ${response}=    POST On Session    api    url=${HEUR_URL}    params=${RULE_PARAMS}
    Should Be Equal As Integers    ${response.status_code}    200
    ${run_id}=    Get From Dictionary    ${response.json()}    run_id
    Sleep    3s
    RETURN    ${run_id}

Get Heuristic Check IDs
    [Documentation]    Get list of check IDs from a completed heuristic run
    [Arguments]    ${run_id}
    ${result}=    GET On Session    api    /api/tests/results/${run_id}
    Should Be Equal As Integers    ${result.status_code}    200
    ${checks}=    Get From Dictionary    ${result.json()}    checks
    ${ids}=    Evaluate    [c["id"] for c in $checks]
    RETURN    ${ids}    ${checks}

*** Test Cases ***
# =============================================================================
# H-RULE HEURISTIC CHECK REGISTRATION — EPIC-RULES-V3-P3
# =============================================================================

Heuristic Run For RULE Domain Returns Results
    [Documentation]    POST /api/tests/heuristic/run?domain=RULE triggers a run that completes.
    [Tags]    heuristic    rule    registration    critical    epic-rules-v3
    ${run_id}=    Trigger Rule Heuristic Run
    ${result}=    GET On Session    api    /api/tests/results/${run_id}
    Should Be Equal As Integers    ${result.status_code}    200
    Should Be Equal As Strings    ${result.json()}[status]    completed

H-RULE-002 Check Appears In Heuristic Results
    [Documentation]    H-RULE-002 (MANDATORY enforcement) must be registered and appear
    ...                in RULE domain heuristic results.
    [Tags]    heuristic    h-rule-002    mandatory    critical    epic-rules-v3
    ${run_id}=    Trigger Rule Heuristic Run
    ${ids}    ${checks}=    Get Heuristic Check IDs    ${run_id}
    Should Contain    ${ids}    H-RULE-002    H-RULE-002 not found in heuristic results

H-RULE-005 Check Appears In Heuristic Results
    [Documentation]    H-RULE-005 (circular dep detection) must be registered and appear
    ...                in RULE domain heuristic results.
    [Tags]    heuristic    h-rule-005    circular    critical    epic-rules-v3
    ${run_id}=    Trigger Rule Heuristic Run
    ${ids}    ${checks}=    Get Heuristic Check IDs    ${run_id}
    Should Contain    ${ids}    H-RULE-005    H-RULE-005 not found in heuristic results

H-RULE-006 Check Appears In Heuristic Results
    [Documentation]    H-RULE-006 (unique IDs) must be registered and appear
    ...                in RULE domain heuristic results.
    [Tags]    heuristic    h-rule-006    unique-ids    critical    epic-rules-v3
    ${run_id}=    Trigger Rule Heuristic Run
    ${ids}    ${checks}=    Get Heuristic Check IDs    ${run_id}
    Should Contain    ${ids}    H-RULE-006    H-RULE-006 not found in heuristic results

RULE Domain Has At Least Five H-RULE Checks
    [Documentation]    With P3 complete, RULE domain should have >=5 H-RULE checks total
    ...                (H-RULE-001 through H-RULE-006, some may be in other split files).
    [Tags]    heuristic    coverage    high    epic-rules-v3
    ${run_id}=    Trigger Rule Heuristic Run
    ${ids}    ${checks}=    Get Heuristic Check IDs    ${run_id}
    ${rule_checks}=    Evaluate    [c for c in $checks if c["id"].startswith("H-RULE-")]
    ${count}=    Get Length    ${rule_checks}
    Should Be True    ${count} >= 5    Expected >=5 H-RULE checks, got ${count}
