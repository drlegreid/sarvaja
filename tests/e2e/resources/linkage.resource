*** Keywords ***
# =============================================================================
# DATA LINKAGE CONSISTENCY TESTS
# Generated from exploratory_linkage_test.py
# =============================================================================

Verify Task Agent Linkage
    [Documentation]    Check tasks have agent_id populated
    [Tags]    linkage    task_agent
    ${tasks}=    Get Tasks Via API
    ${linked}=    Count Items With Field    ${tasks}    agent_id
    ${total}=    Get Length    ${tasks}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Should Be True    ${ratio} >= 0.1    Task-Agent linkage below 10%

Verify Task Session Linkage
    [Documentation]    Check tasks have linked_sessions
    [Tags]    linkage    task_session
    ${tasks}=    Get Tasks Via API
    ${linked}=    Count Items With Non Empty List    ${tasks}    linked_sessions
    ${total}=    Get Length    ${tasks}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Log    Task-Session linkage: ${ratio}

Verify Task Rule Linkage
    [Documentation]    Check tasks have linked_rules
    [Tags]    linkage    task_rule
    ${tasks}=    Get Tasks Via API
    ${linked}=    Count Items With Non Empty List    ${tasks}    linked_rules
    ${total}=    Get Length    ${tasks}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Should Be True    ${ratio} >= 0.3    Task-Rule linkage below 30%

Verify Session Evidence Linkage
    [Documentation]    Check sessions have evidence_files
    [Tags]    linkage    session_evidence
    ${sessions}=    Get Sessions Via API
    ${linked}=    Count Items With Non Empty List    ${sessions}    evidence_files
    ${total}=    Get Length    ${sessions}
    ${ratio}=    Evaluate    ${linked} / ${total} if ${total} > 0 else 0
    Should Be True    ${ratio} >= 0.5    Session-Evidence linkage below 50%

Check Referential Integrity Task Agent
    [Documentation]    Verify task agent_id references exist
    [Tags]    integrity    task_agent
    ${tasks}=    Get Tasks Via API
    ${agents}=    Get Agents Via API
    ${agent_ids}=    Get Field Values    ${agents}    agent_id
    FOR    ${task}    IN    @{tasks}
        ${aid}=    Get From Dictionary    ${task}    agent_id    default=${NONE}
        Continue For Loop If    '${aid}' == 'None'
        Should Contain    ${agent_ids}    ${aid}    Task references non-existent agent
    END

# Helper keywords
Count Items With Field
    [Arguments]    ${items}    ${field}
    ${count}=    Set Variable    0
    FOR    ${item}    IN    @{items}
        ${value}=    Get From Dictionary    ${item}    ${field}    default=${NONE}
        ${count}=    Run Keyword If    '${value}' != 'None' and '${value}' != ''
        ...    Evaluate    ${count} + 1    ELSE    Set Variable    ${count}
    END
    RETURN    ${count}

Count Items With Non Empty List
    [Arguments]    ${items}    ${field}
    ${count}=    Set Variable    0
    FOR    ${item}    IN    @{items}
        ${value}=    Get From Dictionary    ${item}    ${field}    default=${EMPTY}
        ${len}=    Get Length    ${value}
        ${count}=    Run Keyword If    ${len} > 0
        ...    Evaluate    ${count} + 1    ELSE    Set Variable    ${count}
    END
    RETURN    ${count}
