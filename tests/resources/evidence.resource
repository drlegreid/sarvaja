*** Settings ***
Documentation    RF-008: Evidence Collection for Robot Framework Tests
...              Per TEST-FIX-01-v1: Test evidence linked to governance rules
...              Per SESSION-EVID-01-v1: Evidence-based session tracking
Library          Browser    auto_closing_level=KEEP
Library          Collections
Library          DateTime
Library          OperatingSystem
Library          String

*** Variables ***
${EVIDENCE_DIR}      ${CURDIR}/../../evidence
${EVIDENCE_PREFIX}   TEST-RUN

*** Keywords ***
# =============================================================================
# RF-008: EVIDENCE COLLECTION (Per 2026-01-25 implementation)
# =============================================================================

Initialize Evidence Collection
    [Documentation]    Set up evidence collection for test suite
    [Arguments]    ${suite_name}=${SUITE NAME}
    ${date}=    Get Current Date    result_format=%Y-%m-%d
    ${timestamp}=    Get Current Date    result_format=%Y%m%d-%H%M%S
    ${evidence_file}=    Set Variable    ${EVIDENCE_DIR}/${EVIDENCE_PREFIX}-${date}-${suite_name}.md
    Set Suite Variable    ${EVIDENCE_FILE}    ${evidence_file}
    Set Suite Variable    ${SUITE_START}    ${timestamp}
    Set Suite Variable    @{TEST_RESULTS}    @{EMPTY}
    Set Suite Variable    @{LINKED_RULES}    @{EMPTY}

    # Create evidence header line by line
    Create File    ${EVIDENCE_FILE}    \# Test Evidence: ${suite_name}\n
    Append To File    ${EVIDENCE_FILE}    \n
    Append To File    ${EVIDENCE_FILE}    **Date:** ${date}\n
    Append To File    ${EVIDENCE_FILE}    **Suite:** ${suite_name}\n
    Append To File    ${EVIDENCE_FILE}    **Status:** IN_PROGRESS\n
    Append To File    ${EVIDENCE_FILE}    \n
    Append To File    ${EVIDENCE_FILE}    ---\n
    Append To File    ${EVIDENCE_FILE}    \n
    Append To File    ${EVIDENCE_FILE}    \#\# Test Results\n
    Append To File    ${EVIDENCE_FILE}    \n
    Append To File    ${EVIDENCE_FILE}    | Test | Status | Duration | Rule Links |\n
    Append To File    ${EVIDENCE_FILE}    |------|--------|----------|------------|\n
    Log    Evidence collection initialized: ${evidence_file}

Record Test Result
    [Documentation]    Record individual test result with rule linkage
    [Arguments]    ${test_name}    ${status}    ${duration}=0s    @{rules}
    ${rules_str}=    Catenate    SEPARATOR=,    @{rules}
    ${rules_str}=    Set Variable If    '${rules_str}' == ''    -    ${rules_str}
    ${row}=    Set Variable    | ${test_name} | ${status} | ${duration} | ${rules_str} |
    Append To File    ${EVIDENCE_FILE}    ${row}\n

    # Track for summary
    ${result}=    Create Dictionary
    ...    test=${test_name}
    ...    status=${status}
    ...    rules=${rules}
    Append To List    ${TEST_RESULTS}    ${result}

    # Track linked rules
    FOR    ${rule}    IN    @{rules}
        IF    '${rule}' != ''
            Append To List    ${LINKED_RULES}    ${rule}
        END
    END

Link To Rule
    [Documentation]    Associate current test with governance rule
    [Arguments]    ${rule_id}
    Log    Test linked to rule: ${rule_id}
    ${tags}=    Get Variable Value    ${TEST TAGS}    @{EMPTY}
    # Rule ID tracked in test tags

Capture Test Evidence
    [Documentation]    Capture evidence artifacts for current test
    [Arguments]    ${evidence_type}=screenshot    ${name}=${TEST NAME}
    ${timestamp}=    Get Current Date    result_format=%H%M%S
    ${safe_name}=    Replace String    ${name}    ${SPACE}    _
    ${safe_name}=    Convert To Lower Case    ${safe_name}

    IF    '${evidence_type}' == 'screenshot'
        ${screenshot}=    Take Screenshot    ${safe_name}_${timestamp}
        Log    Screenshot captured: ${screenshot}
        RETURN    ${screenshot}
    ELSE IF    '${evidence_type}' == 'html'
        ${html}=    Get Page Source
        ${html_file}=    Set Variable    ${EVIDENCE_DIR}/${safe_name}_${timestamp}.html
        Create File    ${html_file}    ${html}
        Log    HTML captured: ${html_file}
        RETURN    ${html_file}
    ELSE IF    '${evidence_type}' == 'api_response'
        Log    API response evidence type - caller must provide content
        RETURN    ${NONE}
    END

Finalize Evidence Collection
    [Documentation]    Complete evidence file with summary
    ${suite_end}=    Get Current Date    result_format=%Y%m%d-%H%M%S
    ${passed}=    Set Variable    ${0}
    ${failed}=    Set Variable    ${0}

    FOR    ${result}    IN    @{TEST_RESULTS}
        ${status}=    Set Variable    ${result}[status]
        IF    '${status}' == 'PASS'
            ${passed}=    Evaluate    ${passed} + 1
        ELSE
            ${failed}=    Evaluate    ${failed} + 1
        END
    END

    ${total}=    Evaluate    ${passed} + ${failed}
    ${unique_rules}=    Remove Duplicates    ${LINKED_RULES}
    ${rule_count}=    Get Length    ${unique_rules}
    ${rules_list}=    Catenate    SEPARATOR=, @{unique_rules}

    ${summary}=    Catenate    SEPARATOR=\n
    ...
    ...    ---
    ...
    ...    ## Summary
    ...
    ...    - **Total Tests:** ${total}
    ...    - **Passed:** ${passed}
    ...    - **Failed:** ${failed}
    ...    - **Rules Covered:** ${rule_count}
    ...    - **Rule IDs:** ${rules_list}
    ...    - **Start:** ${SUITE_START}
    ...    - **End:** ${suite_end}
    ...
    ...    ---
    ...
    ...    *Per RF-008: Evidence collection automated*
    ...    *Per TEST-FIX-01-v1: Test evidence linked to governance*

    Append To File    ${EVIDENCE_FILE}    ${summary}

    # Update status in file
    ${content}=    Get File    ${EVIDENCE_FILE}
    ${final_status}=    Set Variable If    ${failed} == 0    PASSED    FAILED
    ${content}=    Replace String    ${content}    **Status:** IN_PROGRESS    **Status:** ${final_status}
    Create File    ${EVIDENCE_FILE}    ${content}

    Log    Evidence finalized: ${EVIDENCE_FILE}

# =============================================================================
# TEST HOOKS (for automatic evidence capture)
# =============================================================================

Suite Evidence Setup
    [Documentation]    Call in Suite Setup for automatic evidence collection
    Initialize Evidence Collection

Suite Evidence Teardown
    [Documentation]    Call in Suite Teardown to finalize evidence
    Finalize Evidence Collection

Test Evidence Teardown
    [Documentation]    Call in Test Teardown to record result
    [Arguments]    @{rules}
    ${status}=    Set Variable    ${TEST STATUS}
    ${name}=    Set Variable    ${TEST NAME}
    Record Test Result    ${name}    ${status}    rules=@{rules}
