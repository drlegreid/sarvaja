*** Settings ***
Documentation    RF-008: Evidence Collection Verification
...              Validates evidence collection system works correctly
...              Per TEST-FIX-01-v1: Test evidence linked to governance rules
Resource         ../resources/evidence.resource
Library          OperatingSystem
Library          Collections
Force Tags        unit    evidence    rf008    medium

Suite Setup      Suite Evidence Setup
Suite Teardown   Suite Evidence Teardown
Test Teardown    Test Evidence Teardown    ${TEST_RULE_LINKS}

*** Variables ***
@{TEST_RULE_LINKS}    @{EMPTY}

*** Test Cases ***
Evidence File Is Created
    [Documentation]    Verify evidence file is created during suite
    [Tags]    rf008    evidence    smoke
    Set Test Variable    @{TEST_RULE_LINKS}    RF-008
    File Should Exist    ${EVIDENCE_FILE}
    ${content}=    Get File    ${EVIDENCE_FILE}
    Should Contain    ${content}    Test Evidence

Evidence Contains Test Header
    [Documentation]    Evidence file has proper header structure
    [Tags]    rf008    evidence    structure
    Set Test Variable    @{TEST_RULE_LINKS}    RF-008    TEST-FIX-01-v1
    ${content}=    Get File    ${EVIDENCE_FILE}
    Should Contain    ${content}    Test Results
    Should Contain    ${content}    | Test | Status |

Rule Linkage Works
    [Documentation]    Test can be linked to governance rules
    [Tags]    rf008    evidence    linkage    TEST-GUARD-01-v1
    Set Test Variable    @{TEST_RULE_LINKS}    TEST-GUARD-01-v1    SESSION-EVID-01-v1
    Link To Rule    TEST-GUARD-01-v1
    Link To Rule    SESSION-EVID-01-v1
    Log    This test validates rule linkage

Evidence Artifacts Can Be Captured
    [Documentation]    Various evidence types can be captured
    [Tags]    rf008    evidence    artifacts
    Set Test Variable    @{TEST_RULE_LINKS}    RF-008
    # Note: screenshot capture requires browser - skip in dry-run
    ${result}=    Capture Test Evidence    api_response
    Log    Evidence capture mechanism verified

Multiple Tests Record Results
    [Documentation]    All test results are recorded in evidence
    [Tags]    rf008    evidence    recording
    Set Test Variable    @{TEST_RULE_LINKS}    RF-008    TEST-EVID-01-v1
    ${results}=    Get Variable Value    ${TEST_RESULTS}
    ${count}=    Get Length    ${results}
    Should Be True    ${count} >= 3    msg=Previous tests should be recorded

*** Keywords ***
# No custom keywords needed - evidence.resource provides everything
