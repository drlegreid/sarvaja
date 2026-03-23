*** Settings ***
Documentation    API Testing Keywords
...              Per RF-001: REST API test keywords
...              Per TEST-COMP-01-v1: Deterministic assertions

Library    RequestsLibrary
Library    Collections
Library    JSONLibrary

*** Variables ***
${API_URL}         http://localhost:8082/api
${CONTENT_TYPE}    application/json

*** Keywords ***
Create API Session
    [Documentation]    Create HTTP session for API testing
    [Tags]    api
    Create Session    api    ${API_URL}    verify=${False}

API GET
    [Documentation]    Send GET request to API endpoint
    [Arguments]    ${endpoint}    ${params}=${None}
    [Tags]    api
    ${response}=    GET On Session    api    ${endpoint}    params=${params}    expected_status=any
    RETURN    ${response}

API POST
    [Documentation]    Send POST request to API endpoint
    [Arguments]    ${endpoint}    ${data}=${None}
    [Tags]    api
    ${headers}=    Create Dictionary    Content-Type=${CONTENT_TYPE}
    ${response}=    POST On Session    api    ${endpoint}    json=${data}    headers=${headers}    expected_status=any
    RETURN    ${response}

API PUT
    [Documentation]    Send PUT request to API endpoint
    [Arguments]    ${endpoint}    ${data}=${None}
    [Tags]    api
    ${headers}=    Create Dictionary    Content-Type=${CONTENT_TYPE}
    ${response}=    PUT On Session    api    ${endpoint}    json=${data}    headers=${headers}    expected_status=any
    RETURN    ${response}

API DELETE
    [Documentation]    Send DELETE request to API endpoint
    [Arguments]    ${endpoint}
    [Tags]    api
    ${response}=    DELETE On Session    api    ${endpoint}    expected_status=any
    RETURN    ${response}

Response Status Should Be
    [Documentation]    Verify response status code
    [Arguments]    ${response}    ${expected_status}
    [Tags]    api    assertion
    Should Be Equal As Integers    ${response.status_code}    ${expected_status}

Response Should Contain
    [Documentation]    Verify response body contains key
    [Arguments]    ${response}    ${key}
    [Tags]    api    assertion
    ${json}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${json}    ${key}

Health Check Should Pass
    [Documentation]    Verify API health endpoint returns 200
    [Tags]    api    smoke
    Create API Session
    ${response}=    API GET    /health
    Response Status Should Be    ${response}    200

# ── Task quality keywords (Phase B — EPIC-TASK-QUALITY-V1) ──

Create Test Task
    [Documentation]    Create a task via API for E2E testing. Returns response.
    [Arguments]    ${task_id}    ${summary}    ${task_type}=test    ${priority}=LOW    ${workspace_id}=${None}
    [Tags]    api    tasks
    ${payload}=    Create Dictionary
    ...    task_id=${task_id}
    ...    description=${summary}
    ...    summary=${summary}
    ...    task_type=${task_type}
    ...    priority=${priority}
    ...    phase=P10
    IF    $workspace_id is not None
        Set To Dictionary    ${payload}    workspace_id=${workspace_id}
    END
    ${response}=    API POST    /tasks    ${payload}
    RETURN    ${response}

Cleanup Test Task
    [Documentation]    Delete a test task. Ignores 404.
    [Arguments]    ${task_id}
    [Tags]    api    tasks
    ${response}=    API DELETE    /tasks/${task_id}
    Log    Cleanup ${task_id}: ${response.status_code}

Update Task To Done
    [Documentation]    PUT task to DONE with all mandatory fields.
    [Arguments]    ${task_id}    ${summary}    ${session_id}=SESSION-RF-QUAL-TEST    ${doc_path}=.claude/plans/bubbly-enchanting-eagle.md
    [Tags]    api    tasks
    ${payload}=    Create Dictionary
    ...    status=DONE
    ...    agent_id=code-agent
    ...    summary=${summary}
    ...    linked_sessions=${{["${session_id}"]}}
    ...    linked_documents=${{["${doc_path}"]}}
    ${response}=    API PUT    /tasks/${task_id}    ${payload}
    RETURN    ${response}
