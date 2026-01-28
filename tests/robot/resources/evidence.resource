*** Settings ***
Documentation    RF-008: Evidence Collection Resource
...              Keywords and variables for governance evidence collection
...              Per TEST-FIX-01-v1: Test evidence linked to governance rules
Library          Collections
Library          OperatingSystem
Library          DateTime
Library          ../../libs/BDDEvidenceLibrary.py

*** Variables ***
${EVIDENCE_DIR}        ${CURDIR}/../../../evidence
${EVIDENCE_FILE}       ${EMPTY}
@{TEST_RESULTS}        @{EMPTY}
@{LINKED_RULES}        @{EMPTY}
${RUN_ID}              ${EMPTY}

*** Keywords ***
Suite Evidence Setup
    [Documentation]    Initialize evidence collection for test suite
    Create Directory    ${EVIDENCE_DIR}
    ${timestamp}=    Get Current Date    result_format=%Y%m%d-%H%M%S
    ${run_id}=    Set Variable    TEST-RUN-${timestamp}
    Set Suite Variable    ${RUN_ID}    ${run_id}
    ${file}=    Set Variable    ${EVIDENCE_DIR}/${run_id}.md
    Set Suite Variable    ${EVIDENCE_FILE}    ${file}
    Set Suite Variable    @{TEST_RESULTS}    @{EMPTY}
    Create File    ${file}    # Test Evidence: ${run_id}\n\n| Test | Status | Rules |\n|------|--------|-------|\n

Suite Evidence Teardown
    [Documentation]    Finalize evidence collection and save summary
    ${content}=    Get File    ${EVIDENCE_FILE}
    ${test_count}=    Get Length    ${TEST_RESULTS}
    Append To File    ${EVIDENCE_FILE}    \n---\n\n**Summary:** ${test_count} tests executed\n

Test Evidence Teardown
    [Documentation]    Record test result in evidence file
    [Arguments]    @{rule_links}
    ${test_name}=    Get Variable Value    ${TEST_NAME}
    ${test_status}=    Get Variable Value    ${TEST_STATUS}
    ${rules}=    Catenate    SEPARATOR=,    @{rule_links}
    ${row}=    Set Variable    | ${test_name} | ${test_status} | ${rules} |\n
    Append To File    ${EVIDENCE_FILE}    ${row}
    ${results}=    Get Variable Value    @{TEST_RESULTS}
    ${new_result}=    Create Dictionary    name=${test_name}    status=${test_status}    rules=${rules}
    Append To List    ${results}    ${new_result}
    Set Suite Variable    @{TEST_RESULTS}    @{results}

Link To Rule
    [Documentation]    Link current test to a governance rule
    [Arguments]    ${rule_id}
    Log    Linking to rule: ${rule_id}
    ${linked}=    Get Variable Value    @{LINKED_RULES}    @{EMPTY}
    Append To List    ${linked}    ${rule_id}
    Set Test Variable    @{LINKED_RULES}    @{linked}

Capture Test Evidence
    [Documentation]    Capture evidence artifact from test execution
    [Arguments]    ${artifact_type}
    ${timestamp}=    Get Current Date    result_format=%Y%m%d-%H%M%S
    ${artifact_file}=    Set Variable    ${EVIDENCE_DIR}/artifact-${timestamp}-${artifact_type}.txt
    Log    Capturing ${artifact_type} evidence to ${artifact_file}
    RETURN    ${artifact_file}

Assert Test Linked To Rule
    [Documentation]    Verify test is linked to specified rule
    [Arguments]    ${rule_id}
    ${linked}=    Get Variable Value    @{LINKED_RULES}    @{EMPTY}
    List Should Contain Value    ${linked}    ${rule_id}    msg=Test not linked to ${rule_id}

Get Evidence File Path
    [Documentation]    Return current evidence file path
    RETURN    ${EVIDENCE_FILE}

Get Test Count
    [Documentation]    Return number of tests recorded in this run
    ${results}=    Get Variable Value    @{TEST_RESULTS}    @{EMPTY}
    ${count}=    Get Length    ${results}
    RETURN    ${count}
