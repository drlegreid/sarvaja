*** Settings ***
Documentation    Task Link Structured Error E2E Tests — SRVJ-BUG-ERROR-OBS-01
...              Per TEST-E2E-01-v1: Tier 2 structured error response verification.
...              Proves: Link API responses include success + already_existed + reason fields.
...              Per EPIC-TASK-WORKFLOW-HEAL-01 P3: Structured Error Returns.

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Suite Setup       Setup Structured Error Suite
Suite Teardown    Teardown Structured Error Suite

Default Tags    e2e    api    structured-errors    linking

*** Variables ***
# Per TEST-DATA-01-v1: sandbox workspace only
${TEST_WS}                  WS-TEST-SANDBOX
${SERR_TASK_SESS}           E2E-SERR-SESS-001
${SERR_TASK_DOC}            E2E-SERR-DOC-001
${TEST_SESSION}             SESSION-E2E-SERR-TEST
${TEST_DOC}                 docs/RULES-DIRECTIVES.md

*** Keywords ***
Setup Structured Error Suite
    [Documentation]    Create test tasks in WS-TEST-SANDBOX. Per TEST-DATA-01-v1.
    Create API Session
    api.Create Test Task    ${SERR_TASK_SESS}    Testing > Linking > StructuredError > Session
    ...    task_type=test    workspace_id=${TEST_WS}
    api.Create Test Task    ${SERR_TASK_DOC}     Testing > Linking > StructuredError > Document
    ...    task_type=test    workspace_id=${TEST_WS}

Teardown Structured Error Suite
    [Documentation]    Clean up test tasks.
    api.Cleanup Test Task    ${SERR_TASK_SESS}
    api.Cleanup Test Task    ${SERR_TASK_DOC}

*** Test Cases ***
# =============================================================================
# T2: Session Link — Structured Success Response
# =============================================================================

Session Link Success Returns Structured Response
    [Documentation]    POST session link returns body with success + already_existed fields.
    ...                Per SRVJ-BUG-ERROR-OBS-01: Not just {"linked": true}.
    [Tags]    e2e    api    structured-errors    session    success
    ${resp}=    API POST    /tasks/${SERR_TASK_SESS}/sessions/${TEST_SESSION}
    Response Status Should Be    ${resp}    201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    success
    ...    msg=Session link response must include 'success' field
    Dictionary Should Contain Key    ${json}    already_existed
    ...    msg=Session link response must include 'already_existed' field

Session Link Idempotent Returns Already Existed
    [Documentation]    Second POST to same session returns already_existed=True.
    [Tags]    e2e    api    structured-errors    session    idempotent
    # First link (may already exist from prior test)
    API POST    /tasks/${SERR_TASK_SESS}/sessions/${TEST_SESSION}
    # Second link — must flag idempotency
    ${resp}=    API POST    /tasks/${SERR_TASK_SESS}/sessions/${TEST_SESSION}
    Response Status Should Be    ${resp}    201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    already_existed
    # already_existed should be True on second call
    ${flag}=    Get From Dictionary    ${json}    already_existed
    Should Be True    ${flag}    msg=Second session link should set already_existed=True

# =============================================================================
# T2: Document Link — Structured Success Response
# =============================================================================

Document Link Success Returns Structured Response
    [Documentation]    POST document link returns body with success + already_existed fields.
    [Tags]    e2e    api    structured-errors    document    success
    ${payload}=    Create Dictionary    document_path=${TEST_DOC}
    ${resp}=    API POST    /tasks/${SERR_TASK_DOC}/documents    ${payload}
    Response Status Should Be    ${resp}    201
    ${json}=    Set Variable    ${resp.json()}
    Dictionary Should Contain Key    ${json}    success
    ...    msg=Document link response must include 'success' field
    Dictionary Should Contain Key    ${json}    already_existed
    ...    msg=Document link response must include 'already_existed' field

# =============================================================================
# T2: Session Link — Structured Error Response
# =============================================================================

Session Link Nonexistent Task Returns Structured Error
    [Documentation]    POST with nonexistent task returns error with reason + entity context.
    ...                Per SRVJ-BUG-ERROR-OBS-01: Not just "Failed to create link".
    [Tags]    e2e    api    structured-errors    session    error
    ${resp}=    API POST    /tasks/T-NONEXISTENT-E2E-999/sessions/${TEST_SESSION}
    # Should return 400 (current) or 404, not 500
    ${status}=    Set Variable    ${resp.status_code}
    Should Be True    ${status} < 500    msg=Nonexistent task link should not return 500
    ${json}=    Set Variable    ${resp.json()}
    ${detail}=    Get From Dictionary    ${json}    detail
    Should Contain    ${detail}    not found
    ...    msg=Error detail must include 'not found' reason, got: ${detail}
