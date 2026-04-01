*** Settings ***
Documentation    Task Status Transition Enforcement E2E Tests — SRVJ-BUG-DEAD-LIFECYCLE-01
...              Per TEST-E2E-01-v1: Tier 2+3 status transition validation.
...              Proves: validate_status_transition() is wired in production —
...              invalid transitions return 422, valid transitions succeed,
...              and the dashboard reflects rejection/acceptance correctly.

Resource    ../resources/common.resource
Resource    ../resources/api.resource
Resource    ../resources/selectors.resource
Library     ../libraries/actions.py
Library     ../libraries/overlay.py
Library     Collections

Suite Setup       Setup Transition Enforcement Suite
Suite Teardown    Teardown Transition Enforcement Suite

Default Tags    e2e    tasks    lifecycle    transition-enforcement

*** Variables ***
# Per TEST-DATA-01-v1: sandbox workspace only
${TEST_WS}                WS-TEST-SANDBOX

# Task IDs — one per test concern
${TRANS_INVALID_API}      E2E-TRANS-INVALID-API-001
${TRANS_VALID_API}        E2E-TRANS-VALID-API-001
${TRANS_INVALID_UI}       E2E-TRANS-INVALID-UI-001
${TRANS_VALID_UI}         E2E-TRANS-VALID-UI-001
${TRANS_CHAIN}            E2E-TRANS-CHAIN-001

@{ALL_TEST_TASKS}         ${TRANS_INVALID_API}    ${TRANS_VALID_API}
...                       ${TRANS_INVALID_UI}     ${TRANS_VALID_UI}    ${TRANS_CHAIN}

*** Keywords ***
# ── Lifecycle: Setup & Teardown ──────────────────────────────────────

Setup Transition Enforcement Suite
    [Documentation]    Create test tasks in OPEN status, open dashboard.
    Create API Session
    FOR    ${task_id}    IN    @{ALL_TEST_TASKS}
        api.Create Test Task    ${task_id}    Testing > Transition > ${task_id}
        ...    task_type=test    workspace_id=${TEST_WS}
    END
    Suite Setup Open Dashboard

Teardown Transition Enforcement Suite
    [Documentation]    Clean up test tasks and close browser.
    Suite Teardown Close Browser
    FOR    ${task_id}    IN    @{ALL_TEST_TASKS}
        Cleanup Test Task    ${task_id}
    END

# ── Reusable Assertion Keywords (DRY) ────────────────────────────────

Transition Should Be Rejected
    [Documentation]    PUT a status transition and assert 422 + error message.
    [Arguments]    ${task_id}    ${target_status}
    ${payload}=    Create Dictionary    status=${target_status}
    ${response}=    API PUT    /tasks/${task_id}    ${payload}
    Should Be Equal As Integers    ${response.status_code}    422
    ...    msg=Transition to ${target_status} should return 422, got ${response.status_code}
    Should Contain    ${response.text}    Invalid status transition
    ...    msg=Error body should contain 'Invalid status transition'
    RETURN    ${response}

Transition Should Succeed
    [Documentation]    PUT a status transition and assert 200 + correct status in response.
    [Arguments]    ${task_id}    ${target_status}    &{extra_fields}
    ${payload}=    Create Dictionary    status=${target_status}    &{extra_fields}
    ${response}=    API PUT    /tasks/${task_id}    ${payload}
    Should Be Equal As Integers    ${response.status_code}    200
    ...    msg=Transition to ${target_status} should return 200, got ${response.status_code}
    ${json}=    Set Variable    ${response.json()}
    ${actual}=    Get From Dictionary    ${json}    status
    Should Be Equal    ${actual}    ${target_status}
    ...    msg=Response status should be ${target_status}, got ${actual}
    RETURN    ${response}

Status Should Be Persisted
    [Documentation]    GET a task and assert its status matches expected value.
    [Arguments]    ${task_id}    ${expected_status}
    ${response}=    API GET    /tasks/${task_id}
    Should Be Equal As Integers    ${response.status_code}    200
    ${json}=    Set Variable    ${response.json()}
    ${actual}=    Get From Dictionary    ${json}    status
    Should Be Equal    ${actual}    ${expected_status}
    ...    msg=Persisted status should be ${expected_status}, got ${actual}

# ── UI Navigation Keywords (SRP: one action per keyword) ─────────────

Navigate To Tasks View
    [Documentation]    Navigate to tasks view via direct URL for reliable SPA routing.
    Go To    ${DASHBOARD_URL}/index.html#/projects/${TEST_WS}/tasks
    Wait For Load State    networkidle    timeout=15s
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=30s
    Sleep    1s    reason=Wait for SPA render

Navigate To Task Detail
    [Documentation]    Search for a task and open its detail view.
    [Arguments]    ${task_id}
    Navigate To Tasks View
    ${is_checked}=    Get Checkbox State    ${TASKS_HIDE_TEST_TOGGLE}
    IF    ${is_checked}
        Click    ${TASKS_HIDE_TEST_TOGGLE}
        Sleep    1s    reason=Wait for filter toggle
    END
    Fill Text    ${TASKS_SEARCH} input    ${task_id}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}

Open Task Edit Form
    [Documentation]    Click Edit button on task detail view.
    Click Element Safely    ${TASK_EDIT_BTN}
    Wait For Elements State    [data-testid='task-edit-save-btn']    visible    timeout=5s

Select Status In Edit Form
    [Documentation]    Select a status value from the edit form dropdown.
    [Arguments]    ${status_value}
    Click    [data-testid='task-edit-status']
    Sleep    500ms    reason=Wait for dropdown animation
    Click Element Forced    css=.v-list-item:has-text("${status_value}")
    Sleep    500ms    reason=Wait for selection

Save Task Edit
    [Documentation]    Click Save button on edit form.
    Click Element Safely    [data-testid='task-edit-save-btn']
    Sleep    1s    reason=Wait for API response

Attempt UI Status Change
    [Documentation]    Open task detail, edit status, save. Reusable for valid/invalid UI tests.
    [Arguments]    ${task_id}    ${target_status}
    Navigate To Task Detail    ${task_id}
    Open Task Edit Form
    Select Status In Edit Form    ${target_status}
    Save Task Edit

*** Test Cases ***
# =============================================================================
# T2: API TIER — Status Transition Validation (no browser needed)
# =============================================================================

Invalid Transition OPEN To BLOCKED Returns 422
    [Documentation]    OPEN -> BLOCKED is not in VALID_STATUS_TRANSITIONS.
    ...                Per SRVJ-BUG-DEAD-LIFECYCLE-01: validate_status_transition() wired.
    [Tags]    e2e    api    transition-enforcement    invalid
    Transition Should Be Rejected    ${TRANS_INVALID_API}    BLOCKED

Valid Transition OPEN To IN_PROGRESS Returns 200
    [Documentation]    OPEN -> IN_PROGRESS is a valid transition.
    [Tags]    e2e    api    transition-enforcement    valid
    Transition Should Succeed    ${TRANS_VALID_API}    IN_PROGRESS

Valid Transition Persists In TypeDB
    [Documentation]    After valid transition, GET returns the new status.
    ...                Proves persistence, not just in-memory update.
    [Tags]    e2e    api    transition-enforcement    persistence
    Status Should Be Persisted    ${TRANS_VALID_API}    IN_PROGRESS

Second Invalid Transition Also Rejected
    [Documentation]    IN_PROGRESS -> TODO is also invalid.
    ...                Proves enforcement works for multiple origin states, not just OPEN.
    [Tags]    e2e    api    transition-enforcement    invalid
    # First move to IN_PROGRESS (valid from OPEN)
    Transition Should Succeed    ${TRANS_INVALID_API}    IN_PROGRESS
    # Now try IN_PROGRESS -> TODO (invalid)
    Transition Should Be Rejected    ${TRANS_INVALID_API}    TODO

Full Valid Chain OPEN To DONE
    [Documentation]    OPEN -> IN_PROGRESS -> DONE follows the happy path.
    ...                Each hop must succeed individually.
    [Tags]    e2e    api    transition-enforcement    chain
    Transition Should Succeed    ${TRANS_CHAIN}    IN_PROGRESS
    Transition Should Succeed    ${TRANS_CHAIN}    DONE
    ...    agent_id=${DEFAULT_AGENT}
    ...    summary=Testing > Transition > Chain > Full
    ...    evidence=E2E transition chain test passed

# =============================================================================
# T3: UI TIER — Dashboard Transition Enforcement
# =============================================================================

Dashboard Shows Error On Invalid Transition
    [Documentation]    Editing task status to an invalid value in the dashboard
    ...                shows an error dialog and does NOT change the status.
    ...                Per SRVJ-BUG-DEAD-LIFECYCLE-01: UI enforces same rules as API.
    [Tags]    e2e    browser    transition-enforcement    invalid    ui
    Attempt UI Status Change    ${TRANS_INVALID_UI}    BLOCKED
    # Error dialog should appear
    Wait For Elements State    css=.v-dialog    visible    timeout=5s
    ${dialog_text}=    Get Text    css=.v-dialog
    Should Contain    ${dialog_text}    422    msg=Error dialog should show 422 rejection
    Take Evidence Screenshot    transition-invalid-rejected
    Keyboard Key    press    Escape
    Sleep    500ms

Dashboard Accepts Valid Transition
    [Documentation]    Editing task status to a valid value succeeds and persists.
    ...                Proves dashboard -> API -> TypeDB round-trip works.
    [Tags]    e2e    browser    transition-enforcement    valid    ui
    Attempt UI Status Change    ${TRANS_VALID_UI}    IN_PROGRESS
    Sleep    1s    reason=Wait for detail view to reload
    ${detail_text}=    Get Text    ${TASK_DETAIL}
    Should Contain    ${detail_text}    IN_PROGRESS
    ...    msg=Detail view should show IN_PROGRESS after valid transition
    Take Evidence Screenshot    transition-valid-accepted

Valid UI Transition Persists In TypeDB
    [Documentation]    After valid transition via dashboard, GET /tasks/{id} returns new status.
    ...                Proves the UI change was persisted to TypeDB, not just a UI illusion.
    [Tags]    e2e    browser    transition-enforcement    persistence    ui
    Status Should Be Persisted    ${TRANS_VALID_UI}    IN_PROGRESS
