*** Settings ***
Documentation    Task Link Idempotency E2E Tests — SRVJ-BUG-IDEMP-LINK-01
...              Per TEST-E2E-01-v1: Tier 2+3 idempotency verification.
...              Proves: Session and document link idempotency via REST API.
...              Workspace + commit links have no REST routes — covered by T1 unit tests
...              and MCP tool tests (test_mcp_tasks_linking.py).

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Suite Setup       Setup Idempotency Suite
Suite Teardown    Teardown Idempotency Suite

Default Tags    e2e    api    idempotency    linking

*** Variables ***
${IDEM_TASK_SESS}     E2E-IDEM-SESS-001
${IDEM_TASK_DOC}      E2E-IDEM-DOC-001
${TEST_WORKSPACE}     WS-TEST-SANDBOX
${TEST_SESSION}       SESSION-E2E-IDEM-TEST

*** Keywords ***
Setup Idempotency Suite
    [Documentation]    Create test tasks in WS-TEST-SANDBOX. Per TEST-DATA-01-v1.
    Create API Session
    api.Create Test Task    ${IDEM_TASK_SESS}    Testing > Linking > Session > Idempotent
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}
    api.Create Test Task    ${IDEM_TASK_DOC}     Testing > Linking > Document > Idempotent
    ...    task_type=test    workspace_id=${TEST_WORKSPACE}

Teardown Idempotency Suite
    [Documentation]    Clean up test tasks.
    api.Cleanup Test Task    ${IDEM_TASK_SESS}
    api.Cleanup Test Task    ${IDEM_TASK_DOC}

*** Test Cases ***
Session Link Idempotent Via API
    [Documentation]    Linking same session twice via API doesn't create duplicates.
    ...                Uses _relation_exists helper (retrofitted per SRVJ-BUG-IDEMP-LINK-01).
    [Tags]    e2e    idempotency    session
    # Link session twice
    ${resp1}=    API POST    /tasks/${IDEM_TASK_SESS}/sessions/${TEST_SESSION}
    Response Status Should Be    ${resp1}    201
    ${resp2}=    API POST    /tasks/${IDEM_TASK_SESS}/sessions/${TEST_SESSION}
    # Second call should also succeed (idempotent)
    Response Status Should Be    ${resp2}    201
    # Get sessions and check for duplicates
    ${response}=    API GET    /tasks/${IDEM_TASK_SESS}/sessions
    ${json}=    Set Variable    ${response.json()}
    ${sessions}=    Get From Dictionary    ${json}    sessions
    # Count occurrences of our test session
    ${count}=    Set Variable    ${0}
    FOR    ${s}    IN    @{sessions}
        IF    "${s}" == "${TEST_SESSION}"
            ${count}=    Evaluate    ${count} + 1
        END
    END
    Should Be True    ${count} <= 1    msg=Session link should be idempotent (got ${count} entries for ${TEST_SESSION})

Document Link Idempotent Via API
    [Documentation]    Linking same document twice via API doesn't create duplicates.
    ...                Uses _relation_exists helper (retrofitted per FIX-DATA-005 + SRVJ-BUG-IDEMP-LINK-01).
    [Tags]    e2e    idempotency    document
    # Link same document twice
    ${payload}=    Create Dictionary    document_path=docs/RULES-DIRECTIVES.md
    ${resp1}=    API POST    /tasks/${IDEM_TASK_DOC}/documents    ${payload}
    Response Status Should Be    ${resp1}    201
    ${resp2}=    API POST    /tasks/${IDEM_TASK_DOC}/documents    ${payload}
    Response Status Should Be    ${resp2}    201
    # Get documents and check for duplicates
    ${response}=    API GET    /tasks/${IDEM_TASK_DOC}/documents
    ${json}=    Set Variable    ${response.json()}
    ${docs}=    Get From Dictionary    ${json}    documents
    ${count}=    Get Length    ${docs}
    Should Be True    ${count} <= 1    msg=Document link should be idempotent (got ${count} entries)
