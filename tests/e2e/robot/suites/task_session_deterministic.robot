*** Settings ***
Documentation    P9: Deterministic Session Identity E2E Tests — BUG-SESSION-POISON-01
...              Per TEST-E2E-01-v1: Tier 2+3 verification.
...              Proves: No auto-linking, explicit session_id only, path traversal rejected.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Suite Setup       Setup Deterministic Session Suite
Suite Teardown    Teardown Deterministic Session Suite

Default Tags    e2e    api    security    session-identity

*** Variables ***
${TASK_NO_SESSION}       E2E-DETERM-001
${TASK_WITH_SESSION}     E2E-DETERM-002
${TASK_LINK_TARGET}      E2E-DETERM-003
${TEST_WORKSPACE}        WS-TEST-SANDBOX
${VALID_SESSION}         SESSION-E2E-DETERM-TEST

*** Keywords ***
Setup Deterministic Session Suite
    [Documentation]    Create test tasks in WS-TEST-SANDBOX. Per TEST-DATA-01-v1.
    Create API Session

Teardown Deterministic Session Suite
    [Documentation]    Clean up test tasks.
    api.Cleanup Test Task    ${TASK_NO_SESSION}
    api.Cleanup Test Task    ${TASK_WITH_SESSION}
    api.Cleanup Test Task    ${TASK_LINK_TARGET}

*** Test Cases ***
Task Created Without Session Has Empty Linked Sessions
    [Documentation]    BDD: Task created without session_id has no linked session.
    [Tags]    deterministic    no-autolink
    ${payload}=    Create Dictionary
    ...    task_id=${TASK_NO_SESSION}
    ...    description=E2E deterministic session test - no session
    ...    summary=E2E deterministic session test
    ...    task_type=test
    ...    priority=LOW
    ...    phase=P9
    ...    workspace_id=${TEST_WORKSPACE}
    ${response}=    API POST    /tasks    ${payload}
    Response Status Should Be    ${response}    201
    ${json}=    Set Variable    ${response.json()}
    # Key assertion: linked_sessions must be empty
    ${linked}=    Get From Dictionary    ${json}    linked_sessions    default=${EMPTY}
    ${length}=    Get Length    ${linked}
    Should Be Equal As Integers    ${length}    0
    ...    msg=Task created without session_id should have empty linked_sessions, got: ${linked}

Task Created With Explicit Session Links Correctly
    [Documentation]    BDD: Task created with explicit session_id links correctly.
    [Tags]    deterministic    explicit-link
    ${sessions}=    Create List    ${VALID_SESSION}
    ${payload}=    Create Dictionary
    ...    task_id=${TASK_WITH_SESSION}
    ...    description=E2E deterministic session test - with session
    ...    summary=E2E deterministic session test
    ...    task_type=test
    ...    priority=LOW
    ...    phase=P9
    ...    workspace_id=${TEST_WORKSPACE}
    ...    linked_sessions=${sessions}
    ${response}=    API POST    /tasks    ${payload}
    Response Status Should Be    ${response}    201
    ${json}=    Set Variable    ${response.json()}
    ${linked}=    Get From Dictionary    ${json}    linked_sessions
    List Should Contain Value    ${linked}    ${VALID_SESSION}

Session Create With Path Traversal Returns 422
    [Documentation]    BDD: POST /api/sessions with path traversal → 422.
    [Tags]    deterministic    security    path-traversal
    ${payload}=    Create Dictionary
    ...    session_id=../../etc/passwd
    ...    session_type=CC
    ${response}=    API POST    /sessions    ${payload}
    Response Status Should Be    ${response}    422

Task Link Session With Path Traversal Rejected
    [Documentation]    BDD: POST /api/tasks/{id}/sessions/{path_traversal} → rejected.
    [Tags]    deterministic    security    path-traversal
    # First create a task to link
    ${payload}=    Create Dictionary
    ...    task_id=${TASK_LINK_TARGET}
    ...    description=E2E link target for path traversal test
    ...    summary=E2E link target
    ...    task_type=test
    ...    priority=LOW
    ...    phase=P9
    ...    workspace_id=${TEST_WORKSPACE}
    ${create_resp}=    API POST    /tasks    ${payload}
    Response Status Should Be    ${create_resp}    201
    # Try to link with path traversal session_id
    ${link_resp}=    API POST    /tasks/${TASK_LINK_TARGET}/sessions/..%2F..%2Fetc%2Fpasswd
    # Should be rejected — either 400 or 422 or 500 with error
    ${status}=    Set Variable    ${link_resp.status_code}
    Should Not Be Equal As Integers    ${status}    201
    ...    msg=Path traversal session link should NOT succeed with 201
