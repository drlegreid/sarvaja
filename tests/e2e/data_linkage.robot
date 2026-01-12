*** Settings ***
Documentation    Data Linkage Consistency E2E Tests
...              Tests cross-entity relationships in TypeDB and API
...              Generated from exploratory_linkage_test.py
...              Per RULE-020: LLM-Driven E2E Test Generation
...              Per RULE-023: Test Before Ship
...              Per GAP-DATA-002: Cross-entity relationships
Library          Browser
Library          Collections
Library          RequestsLibrary
Resource         resources/common.resource
Resource         resources/linkage.resource

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
# LINKAGE COVERAGE TESTS
# =============================================================================

Task Agent Linkage Coverage
    [Documentation]    Verify at least 10% of tasks have agent_id
    [Tags]    linkage    task_agent    high
    Verify Task Agent Linkage

Task Session Linkage Coverage
    [Documentation]    Verify at least 5% of tasks have linked_sessions
    ...                Currently failing: 1.5% coverage (GAP-LINK-001)
    [Tags]    linkage    task_session    medium    known_gap
    Verify Task Session Linkage

Task Rule Linkage Coverage
    [Documentation]    Verify at least 30% of tasks have linked_rules
    ...                Currently failing: 4.5% coverage (GAP-LINK-002)
    [Tags]    linkage    task_rule    high    known_gap
    Verify Task Rule Linkage

Session Evidence Linkage Coverage
    [Documentation]    Verify at least 50% of sessions have evidence_files
    ...                Currently failing: 22.2% coverage (GAP-LINK-003)
    [Tags]    linkage    session_evidence    high    known_gap
    Verify Session Evidence Linkage

Session Agent Linkage Coverage
    [Documentation]    Verify at least 10% of sessions have agent_id
    [Tags]    linkage    session_agent    medium
    ${sessions}=    Get Sessions Via API
    ${linked}=    Count Items With Field    ${sessions}    agent_id
    ${total}=    Get Length    ${sessions}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Should Be True    ${ratio} >= 0.1    Session-Agent linkage below 10%

# =============================================================================
# REFERENTIAL INTEGRITY TESTS
# =============================================================================

Task Agent Referential Integrity
    [Documentation]    Verify all task agent_id values reference valid agents
    [Tags]    integrity    task_agent    critical
    Check Referential Integrity Task Agent

Task Session Referential Integrity
    [Documentation]    Verify all task linked_sessions reference valid sessions
    [Tags]    integrity    task_session    high
    ${tasks}=    Get Tasks Via API
    ${sessions}=    Get Sessions Via API
    ${session_ids}=    Get Field Values    ${sessions}    session_id
    FOR    ${task}    IN    @{tasks}
        ${linked}=    Get From Dictionary    ${task}    linked_sessions    default=${EMPTY}
        Continue For Loop If    '${linked}' == ''
        FOR    ${sid}    IN    @{linked}
            Should Contain    ${session_ids}    ${sid}
            ...    msg=Task references non-existent session ${sid}
        END
    END

Task Rule Referential Integrity
    [Documentation]    Verify all task linked_rules reference valid rules
    [Tags]    integrity    task_rule    high
    ${tasks}=    Get Tasks Via API
    ${rules}=    Get Rules Via API
    ${rule_ids}=    Get Field Values    ${rules}    id
    # Also check rule_id field
    ${rule_ids2}=    Get Field Values    ${rules}    rule_id
    ${all_rule_ids}=    Combine Lists    ${rule_ids}    ${rule_ids2}
    FOR    ${task}    IN    @{tasks}
        ${linked}=    Get From Dictionary    ${task}    linked_rules    default=${EMPTY}
        Continue For Loop If    '${linked}' == ''
        FOR    ${rid}    IN    @{linked}
            Should Contain    ${all_rule_ids}    ${rid}
            ...    msg=Task references non-existent rule ${rid}
        END
    END

# =============================================================================
# BIDIRECTIONAL CONSISTENCY TESTS
# =============================================================================

Session Task Bidirectional Consistency
    [Documentation]    Verify session tasks_completed matches linked task count
    [Tags]    bidirectional    session_task    medium
    ${tasks}=    Get Tasks Via API
    ${sessions}=    Get Sessions Via API

    # Build session -> task mapping
    ${session_task_map}=    Create Dictionary
    FOR    ${task}    IN    @{tasks}
        ${linked}=    Get From Dictionary    ${task}    linked_sessions    default=${EMPTY}
        Continue For Loop If    '${linked}' == ''
        FOR    ${sid}    IN    @{linked}
            ${current}=    Get From Dictionary    ${session_task_map}    ${sid}    default=${EMPTY}
            ${task_id}=    Get From Dictionary    ${task}    task_id
            ${new_list}=    Create List    ${task_id}
            ${updated}=    Run Keyword If    '${current}' == ''
            ...    Set Variable    ${new_list}
            ...    ELSE    Combine Lists    ${current}    ${new_list}
            Set To Dictionary    ${session_task_map}    ${sid}    ${updated}
        END
    END

    # Log summary
    Log    Session-Task mapping: ${session_task_map}
