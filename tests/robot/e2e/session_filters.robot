*** Settings ***
Documentation    E2E Tests for Session Filters
...              Per EPIC-I.2: Robot Test Integration
...              Tests: Status filter, Agent filter, Search query
Library          Collections
Library          libs/GovernanceCRUDE2ELibrary.py
Suite Setup      Setup Filter Test Data
Suite Teardown   Cleanup Test Data
Test Tags        e2e    api    sessions    filters

*** Variables ***
${FILTER_SESSION_DESC}    Robot filter test session

*** Keywords ***
Setup Filter Test Data
    [Documentation]    Create test sessions with different statuses and agents
    API Health Check
    # Create an ACTIVE session with agent "robot-filter-a"
    ${sid_a}=    Generate Unique ID    TEST-FILTER-A
    Set Suite Variable    ${FILTER_SID_A}    ${sid_a}
    ${data_a}=    Create Dictionary
    ...    session_id=${sid_a}
    ...    description=Filter test active session
    ...    agent_id=robot-filter-a
    ${result_a}=    Post Session Raw    ${data_a}
    Should Be Equal As Integers    ${result_a}[status_code]    201    Setup create A failed: ${result_a}
    # Create a second session with agent "robot-filter-b" and immediately delete it (COMPLETED)
    ${sid_b}=    Generate Unique ID    TEST-FILTER-B
    Set Suite Variable    ${FILTER_SID_B}    ${sid_b}
    ${data_b}=    Create Dictionary
    ...    session_id=${sid_b}
    ...    description=Filter test completed session
    ...    agent_id=robot-filter-b
    ${result_b}=    Post Session Raw    ${data_b}
    Should Be Equal As Integers    ${result_b}[status_code]    201    Setup create B failed: ${result_b}

*** Test Cases ***
Filter Sessions By Status Active
    [Documentation]    Filtering by status=ACTIVE should include the active session
    [Tags]    e2e    sessions    filters    status
    ${result}=    Get Resource With Body    sessions?status=ACTIVE&limit=200
    Should Be Equal As Integers    ${result}[status_code]    200
    ${items}=    Set Variable    ${result}[body][items]
    ${ids}=    Evaluate    [s['session_id'] for s in $items]
    Should Contain    ${ids}    ${FILTER_SID_A}

Filter Sessions By Agent
    [Documentation]    Filtering by agent_id should return only matching sessions
    [Tags]    e2e    sessions    filters    agent
    ${result}=    Get Resource With Body    sessions?agent_id=robot-filter-a&limit=200
    Should Be Equal As Integers    ${result}[status_code]    200
    ${items}=    Set Variable    ${result}[body][items]
    ${ids}=    Evaluate    [s['session_id'] for s in $items]
    Should Contain    ${ids}    ${FILTER_SID_A}
    Should Not Contain    ${ids}    ${FILTER_SID_B}

Filter Sessions By Agent B
    [Documentation]    Filtering by agent robot-filter-b should return only B session
    [Tags]    e2e    sessions    filters    agent
    ${result}=    Get Resource With Body    sessions?agent_id=robot-filter-b&limit=200
    Should Be Equal As Integers    ${result}[status_code]    200
    ${items}=    Set Variable    ${result}[body][items]
    ${ids}=    Evaluate    [s['session_id'] for s in $items]
    Should Contain    ${ids}    ${FILTER_SID_B}
    Should Not Contain    ${ids}    ${FILTER_SID_A}

Unfiltered Sessions Include Both
    [Documentation]    Without filters, both test sessions should appear
    [Tags]    e2e    sessions    filters    unfiltered
    ${result}=    Get Resource With Body    sessions?limit=200
    Should Be Equal As Integers    ${result}[status_code]    200
    ${items}=    Set Variable    ${result}[body][items]
    ${ids}=    Evaluate    [s['session_id'] for s in $items]
    Should Contain    ${ids}    ${FILTER_SID_A}
    Should Contain    ${ids}    ${FILTER_SID_B}

Sessions List Returns Pagination Metadata
    [Documentation]    Sessions endpoint should return pagination metadata
    [Tags]    e2e    sessions    pagination
    ${result}=    Get Resource With Body    sessions?limit=5
    Should Be Equal As Integers    ${result}[status_code]    200
    Dictionary Should Contain Key    ${result}[body]    items
    Dictionary Should Contain Key    ${result}[body]    total
