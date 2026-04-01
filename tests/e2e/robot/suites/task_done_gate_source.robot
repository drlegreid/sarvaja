*** Settings ***
Documentation    DONE Gate Validation Source E2E Tests — SRVJ-BUG-DONE-GATE-01 (P5)
...              Per TEST-E2E-01-v1: Tier 2+3 verification.
...              Proves: PUT task to DONE returns validation_source in response body.
...              Per TEST-DATA-01-v1: Uses WS-TEST-SANDBOX only.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Suite Setup       Setup Done Gate Suite
Suite Teardown    Teardown Done Gate Suite

Default Tags    e2e    api    done-gate    p5

*** Variables ***
${DG_TASK_ID}          SRVJ-TEST-DONEGATE-E2E-001
${TEST_WORKSPACE}      WS-TEST-SANDBOX
${DEFAULT_AGENT}       code-agent

*** Keywords ***
Setup Done Gate Suite
    [Documentation]    Create API session + seed task for DONE gate tests.
    Create API Session
    # Create a chore task (minimal DoD: summary + agent_id)
    ${payload}=    Create Dictionary
    ...    task_id=${DG_TASK_ID}
    ...    description=E2E DONE Gate Validation Source Test
    ...    summary=Testing > DoneGate > ValidationSource > E2E
    ...    task_type=chore
    ...    priority=LOW
    ...    phase=P5
    ...    workspace_id=${TEST_WORKSPACE}
    ${response}=    API POST    /tasks    ${payload}
    Log    Create task: ${response.status_code}
    # Move to IN_PROGRESS first (required transition)
    ${ip_payload}=    Create Dictionary
    ...    status=IN_PROGRESS
    ...    agent_id=${DEFAULT_AGENT}
    ${ip_response}=    API PUT    /tasks/${DG_TASK_ID}    ${ip_payload}
    Log    IN_PROGRESS: ${ip_response.status_code}

Teardown Done Gate Suite
    [Documentation]    Clean up test task.
    api.Cleanup Test Task    ${DG_TASK_ID}

*** Test Cases ***
PUT Task To DONE Returns Validation Source
    [Documentation]    PUT /api/tasks/{id} with status=DONE → response includes validation_source.
    ...                Per SRVJ-BUG-DONE-GATE-01: Caller must know if validation used TypeDB or cache.
    [Tags]    e2e    done-gate    validation-source
    ${payload}=    Create Dictionary
    ...    status=DONE
    ...    agent_id=${DEFAULT_AGENT}
    ...    summary=Testing > DoneGate > ValidationSource > E2E
    ...    linked_sessions=${{["SESSION-RF-DONEGATE-TEST"]}}
    ...    linked_documents=${{[".claude/plans/concurrent-crunching-yao.md"]}}
    ${response}=    API PUT    /tasks/${DG_TASK_ID}    ${payload}
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    Should Be Equal    ${json}[status]    DONE
    Dictionary Should Contain Key    ${json}    validation_source
    Should Be True    '${json}[validation_source]' in ['typedb', 'cache']
