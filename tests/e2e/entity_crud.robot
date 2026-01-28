*** Settings ***
Documentation    Entity Management E2E Tests
...              Per RF-006: E2E test migration to Robot Framework
...              Per TEST-E2E-01-v1: E2E Test Requirements
Library          Collections
Resource         ../resources/common.resource

Suite Setup       Create API Session
Default Tags      e2e    api    crud

*** Test Cases ***
# === RULES ENTITY ===

Verify Rules List
    [Documentation]    Verify rules endpoint returns list
    [Tags]    rules    list
    ${response}=    API GET    /rules
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    isinstance($json, list)    Rules endpoint should return a list

Verify Rules Read Detail
    [Documentation]    Verify individual rule can be retrieved
    [Tags]    rules    read_detail
    ${list_response}=    API GET    /rules
    Response Status Should Be    ${list_response}    200
    ${rules}=    Set Variable    ${list_response.json()}
    Skip If    len($rules) == 0    No rules available to test
    ${first_rule}=    Get From List    ${rules}    0
    # Rules API uses 'id' not 'rule_id'
    ${rule_id}=    Set Variable    ${first_rule['id']}
    ${response}=    API GET    /rules/${rule_id}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json['id']}    ${rule_id}

# === AGENTS ENTITY ===

Verify Agents List
    [Documentation]    Verify agents endpoint returns list
    [Tags]    agents    list
    ${response}=    API GET    /agents
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    isinstance($json, list)    Agents endpoint should return a list

Verify Agents Read Detail
    [Documentation]    Verify individual agent can be retrieved
    [Tags]    agents    read_detail
    ${list_response}=    API GET    /agents
    Response Status Should Be    ${list_response}    200
    ${agents}=    Set Variable    ${list_response.json()}
    Skip If    len($agents) == 0    No agents available to test
    ${first_agent}=    Get From List    ${agents}    0
    ${agent_id}=    Set Variable    ${first_agent['agent_id']}
    ${response}=    API GET    /agents/${agent_id}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json['agent_id']}    ${agent_id}

# === TASKS ENTITY ===

Verify Tasks List
    [Documentation]    Verify tasks endpoint returns list or paginated response
    [Tags]    tasks    list
    ${response}=    API GET    /tasks
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    # Handle paginated or direct list response
    ${is_paginated}=    Run Keyword And Return Status    Dictionary Should Contain Key    ${json}    items
    IF    ${is_paginated}
        ${tasks}=    Get From Dictionary    ${json}    items
        Should Be True    isinstance($tasks, list)
    ELSE
        Should Be True    isinstance($json, list)    Tasks endpoint should return a list
    END

Verify Tasks Create And Delete
    [Documentation]    Verify task can be created and deleted
    [Tags]    tasks    create    delete
    # Generate unique task ID with timestamp
    ${timestamp}=    Evaluate    int(__import__('time').time())
    ${task_id}=    Set Variable    RF-TEST-${timestamp}
    ${task_data}=    Create Dictionary
    ...    task_id=${task_id}
    ...    name=Robot Framework Test Task
    ...    description=Created by Robot Framework e2e test
    ...    status=TODO
    ...    priority=LOW
    ...    phase=P10
    ${create_response}=    API POST    /tasks    ${task_data}
    Response Status Should Be    ${create_response}    201
    ${created}=    Set Variable    ${create_response.json()}
    Should Be Equal    ${created['task_id']}    ${task_id}
    Should Be Equal    ${created['description']}    Created by Robot Framework e2e test
    # Cleanup - delete the test task (204 No Content on success)
    ${delete_response}=    API DELETE    /tasks/${task_id}
    Response Status Should Be    ${delete_response}    204

# === SESSIONS ENTITY ===

Verify Sessions List
    [Documentation]    Verify sessions endpoint returns paginated list
    [Tags]    sessions    list
    ${response}=    API GET    /sessions
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    # Sessions API returns paginated {"items": [...], "pagination": {...}}
    ${is_paginated}=    Run Keyword And Return Status    Dictionary Should Contain Key    ${json}    items
    IF    ${is_paginated}
        ${sessions}=    Get From Dictionary    ${json}    items
        Should Be True    isinstance($sessions, list)
    ELSE
        Should Be True    isinstance($json, list)    Sessions endpoint should return a list
    END

# === DECISIONS ENTITY ===

Verify Decisions List
    [Documentation]    Verify decisions endpoint returns list
    [Tags]    decisions    list
    ${response}=    API GET    /decisions
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    isinstance($json, list)    Decisions endpoint should return a list

*** Variables ***
${CURTIME}    ${EMPTY}

*** Keywords ***
Get Current Timestamp
    ${time}=    Evaluate    int(__import__('time').time())
    RETURN    ${time}
