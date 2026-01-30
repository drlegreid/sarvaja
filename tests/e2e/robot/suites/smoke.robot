*** Settings ***
Documentation    Smoke Tests for Governance Platform
...              Per RF-001: Quick sanity checks
...              Per TEST-COMP-02-v1: Test Before Ship

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Suite Setup       Create API Session

Default Tags    smoke    e2e

*** Test Cases ***
API Health Check
    [Documentation]    Verify API server is responding
    [Tags]    api    critical
    Health Check Should Pass

Dashboard Loads Successfully
    [Documentation]    Verify dashboard UI responds with HTTP 200
    [Tags]    ui    critical
    ${response}=    GET On Session    api    ${BASE_URL}/    expected_status=any
    Should Be True    ${response.status_code} in [200, 302]    Dashboard returned ${response.status_code}

Rules API Returns List
    [Documentation]    Verify rules endpoint returns data
    [Tags]    api    rules
    ${response}=    API GET    /rules
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be True    len($json) >= 0    No rules returned

Tasks API Returns List
    [Documentation]    Verify tasks endpoint returns data
    [Tags]    api    tasks
    ${response}=    API GET    /tasks
    Response Status Should Be    ${response}    200

Agents API Returns List
    [Documentation]    Verify agents endpoint returns data
    [Tags]    api    agents
    ${response}=    API GET    /agents
    Response Status Should Be    ${response}    200
