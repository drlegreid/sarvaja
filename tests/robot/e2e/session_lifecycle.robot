*** Settings ***
Documentation    E2E Tests for Session Lifecycle
...              Per EPIC-I: Robot Test Integration
...              Tests: Create session → verify in list → verify tool_calls → verify thoughts → delete → verify deleted
Library          Collections
Library          libs/GovernanceCRUDE2ELibrary.py
Suite Setup      API Health Check
Suite Teardown   Cleanup Test Data
Test Tags        e2e    api    sessions    lifecycle    SESSION-EVID-01-v1

*** Variables ***
${TEST_SESSION_DESC}    Robot lifecycle test session

*** Test Cases ***
Create Session Via API
    [Documentation]    Create a session and verify it returns 201
    [Tags]    e2e    sessions    create
    ${sid}=    Generate Unique ID    TEST-ROBOT-SESSION
    Set Suite Variable    ${ROBOT_SESSION_ID}    ${sid}
    ${session_data}=    Create Dictionary
    ...    session_id=${sid}
    ...    description=${TEST_SESSION_DESC}
    ...    agent_id=robot-test
    ${result}=    Post Session Raw    ${session_data}
    Should Be Equal As Integers    ${result}[status_code]    201    Create failed: ${result}
    Should Be Equal    ${result}[body][session_id]    ${sid}

Verify Session In List
    [Documentation]    Verify created session appears in sessions list
    [Tags]    e2e    sessions    list
    ${result}=    Get Resource With Body    sessions?limit=50
    Should Be Equal As Integers    ${result}[status_code]    200
    ${items}=    Set Variable    ${result}[body][items]
    ${ids}=    Evaluate    [s['session_id'] for s in $items]
    Should Contain    ${ids}    ${ROBOT_SESSION_ID}

Verify Tool Calls Endpoint
    [Documentation]    Verify tool_calls endpoint returns data for session
    [Tags]    e2e    sessions    tool_calls
    ${result}=    Get Resource With Body    sessions/${ROBOT_SESSION_ID}/tool_calls
    Should Be Equal As Integers    ${result}[status_code]    200
    Should Be Equal    ${result}[body][session_id]    ${ROBOT_SESSION_ID}
    Dictionary Should Contain Key    ${result}[body]    tool_call_count

Verify Thoughts Endpoint
    [Documentation]    Verify thoughts endpoint returns data for session
    [Tags]    e2e    sessions    thoughts
    ${result}=    Get Resource With Body    sessions/${ROBOT_SESSION_ID}/thoughts
    Should Be Equal As Integers    ${result}[status_code]    200
    Should Be Equal    ${result}[body][session_id]    ${ROBOT_SESSION_ID}
    Dictionary Should Contain Key    ${result}[body]    thought_count

Delete Session
    [Documentation]    Deleting a session should return 204
    [Tags]    e2e    sessions    delete
    ${result}=    Delete Resource Raw    sessions/${ROBOT_SESSION_ID}
    Should Be Equal As Integers    ${result}[status_code]    204

Verify Session Deleted
    [Documentation]    Verify session no longer appears in list
    [Tags]    e2e    sessions    verify_delete
    ${result}=    Get Resource With Body    sessions?limit=200
    Should Be Equal As Integers    ${result}[status_code]    200
    ${items}=    Set Variable    ${result}[body][items]
    ${ids}=    Evaluate    [s['session_id'] for s in $items]
    Should Not Contain    ${ids}    ${ROBOT_SESSION_ID}
