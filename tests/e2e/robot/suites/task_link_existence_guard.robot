*** Settings ***
Documentation    SRVJ-BUG-LINK-ORPHAN-01: Tier 2 — Link operations on nonexistent tasks
...              must return structured errors, not create orphan relations.
...              Per EPIC-TASK-WORKFLOW-HEAL-01 Dogfood Quality Sweep.

Resource    ../resources/api.resource

Suite Setup       Setup Guard Tests
Suite Teardown    Cleanup Guard Test Tasks


*** Variables ***
${TEST_WORKSPACE}         WS-TEST-SANDBOX
${GUARD_TASK}             E2E-GUARD-001
${NONEXISTENT_TASK}       E2E-NONEXISTENT-XYZ-999
${TEST_SESSION}           SESSION-E2E-GUARD-TEST
${TEST_RULE}              TEST-E2E-01-v1


*** Test Cases ***

# ── Session Link Guards ──────────────────────────────────────────────

Session Link To Nonexistent Task Returns Error
    [Documentation]    POST /tasks/{nonexistent}/sessions/{id} must NOT return 201.
    ...                Per SRVJ-BUG-LINK-ORPHAN-01: existence check before linking.
    [Tags]    tier2    guard    session
    ${response}=    API POST    /tasks/${NONEXISTENT_TASK}/sessions/${TEST_SESSION}
    # Must NOT be 201 — should be 404 or 400
    ${status}=    Set Variable    ${response.status_code}
    Should Not Be Equal As Integers    ${status}    201
    ...    msg=Link to nonexistent task MUST NOT succeed (got 201)

Session Link To Existing Task Succeeds
    [Documentation]    POST /tasks/{existing}/sessions/{id} returns 201.
    [Tags]    tier2    guard    session
    ${response}=    API POST    /tasks/${GUARD_TASK}/sessions/${TEST_SESSION}
    Response Status Should Be    ${response}    201
    ${json}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${json}    success

Session Link Round Trip Verified
    [Documentation]    After linking, GET /tasks/{id}/sessions includes the linked session.
    [Tags]    tier2    guard    roundtrip
    ${response}=    API GET    /tasks/${GUARD_TASK}/sessions
    Response Status Should Be    ${response}    200
    ${json}=    Set Variable    ${response.json()}
    ${sessions}=    Get From Dictionary    ${json}    sessions
    # API returns session objects — extract session_ids
    ${session_ids}=    Evaluate    [s.get("session_id") for s in $sessions]
    Should Contain    ${session_ids}    ${TEST_SESSION}
    ...    msg=Linked session not found in round-trip read

# ── Rule Link Guards ─────────────────────────────────────────────────

Rule Link To Nonexistent Task Returns Error
    [Documentation]    POST /tasks/{nonexistent}/rules/{id} must NOT return 201.
    [Tags]    tier2    guard    rule
    ${response}=    API POST    /tasks/${NONEXISTENT_TASK}/rules/${TEST_RULE}
    ${status}=    Set Variable    ${response.status_code}
    Should Not Be Equal As Integers    ${status}    201
    ...    msg=Rule link to nonexistent task MUST NOT succeed (got 201)

Rule Link To Existing Task Succeeds
    [Documentation]    POST /tasks/{existing}/rules/{id} returns 201.
    [Tags]    tier2    guard    rule
    ${response}=    API POST    /tasks/${GUARD_TASK}/rules/${TEST_RULE}
    Response Status Should Be    ${response}    201

# ── Document Link Guards ─────────────────────────────────────────────

Document Link To Nonexistent Task Returns Error
    [Documentation]    POST /tasks/{nonexistent}/documents must NOT return 201.
    [Tags]    tier2    guard    document
    ${payload}=    Create Dictionary    document_path=docs/README.md
    ${response}=    API POST    /tasks/${NONEXISTENT_TASK}/documents    ${payload}
    ${status}=    Set Variable    ${response.status_code}
    Should Not Be Equal As Integers    ${status}    201
    ...    msg=Document link to nonexistent task MUST NOT succeed (got 201)


*** Keywords ***

Cleanup Guard Test Tasks
    [Documentation]    Clean up test task created during setup.
    api.Cleanup Test Task    ${GUARD_TASK}

Setup Guard Tests
    [Documentation]    Create API session and test task for guard tests.
    api.Create API Session
    api.Cleanup Test Task    ${GUARD_TASK}
    ${response}=    api.Create Test Task    ${GUARD_TASK}    Guard existence test task
    ...    workspace_id=${TEST_WORKSPACE}
    api.Response Status Should Be    ${response}    201
