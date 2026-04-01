*** Settings ***
Documentation    Agent-ID Standalone Persistence E2E Tests — SRVJ-BUG-AGENTID-PERSIST-01 (P6)
...              Per TEST-E2E-01-v1: Tier 2+3 verification.
...              Proves: PUT /api/tasks/{id} with ONLY agent_id persists to TypeDB.
...              Per TEST-DATA-01-v1: Uses WS-TEST-SANDBOX only.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Suite Setup       Setup AgentId Persist Suite
Suite Teardown    Teardown AgentId Persist Suite

Default Tags    e2e    api    agentid    p6

*** Variables ***
${AID_TASK_ID}         SRVJ-TEST-AGENTID-E2E-001
${TEST_WORKSPACE}      WS-TEST-SANDBOX
${DEFAULT_AGENT}       code-agent
${NEW_AGENT}           research-agent

*** Keywords ***
Setup AgentId Persist Suite
    [Documentation]    Create API session + seed task for agent_id persistence tests.
    Create API Session
    # Create a chore task (minimal DoD) with NO agent_id
    ${payload}=    Create Dictionary
    ...    task_id=${AID_TASK_ID}
    ...    description=E2E Agent-ID Standalone Persistence Test
    ...    summary=Testing > AgentID > Persistence > E2E
    ...    task_type=chore
    ...    priority=LOW
    ...    phase=P6
    ...    workspace_id=${TEST_WORKSPACE}
    ${response}=    API POST    /tasks    ${payload}
    Log    Create task: ${response.status_code}

Teardown AgentId Persist Suite
    [Documentation]    Clean up test task.
    api.Cleanup Test Task    ${AID_TASK_ID}

*** Test Cases ***
PUT Task With Only Agent ID Returns Updated Agent
    [Documentation]    PUT /api/tasks/{id} with ONLY agent_id field → response shows updated agent_id.
    ...                This is the core bug: agent_id-only updates should persist, not silently degrade.
    [Tags]    e2e    agentid    persistence
    ${payload}=    Create Dictionary
    ...    agent_id=${NEW_AGENT}
    ${response}=    API PUT    /tasks/${AID_TASK_ID}    ${payload}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json}[agent_id]    ${NEW_AGENT}

GET Task After Agent ID Update Shows Persisted Value
    [Documentation]    GET /api/tasks/{id} after agent_id-only PUT → agent_id is persisted (not memory-only).
    ...                Verifies the TypeDB write path was triggered, not just _tasks_store.
    [Tags]    e2e    agentid    persistence    read-back
    # First update with agent_id only
    ${put_payload}=    Create Dictionary
    ...    agent_id=${DEFAULT_AGENT}
    ${put_response}=    API PUT    /tasks/${AID_TASK_ID}    ${put_payload}
    Response Status Should Be    ${put_response}    200
    # Now read it back
    ${get_response}=    API GET    /tasks/${AID_TASK_ID}
    Response Status Should Be    ${get_response}    200
    ${json}=    Set Variable    ${get_response.json()}
    Should Be Equal    ${json}[agent_id]    ${DEFAULT_AGENT}
