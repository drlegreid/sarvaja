*** Settings ***
Documentation    Task Linking E2E Tests — EPIC-TASK-QUALITY-V2 Phase 9
...              Per TEST-E2E-01-v1: Tier 3 linking dialog verification.
...              Proves: Link Session dialog, Link Document dialog, persistence.
...              FEAT-011: Session picker dialog
...              FEAT-012: Document tree browser

Resource    ../resources/common.resource
Resource    ../resources/api.resource
Resource    ../resources/selectors.resource
Library     ../libraries/actions.py
Library     ../libraries/overlay.py

Suite Setup       Setup Task Linking Suite
Suite Teardown    Teardown Task Linking Suite
Test Setup        Setup Linking Test

Default Tags    e2e    browser    tasks    linking

*** Variables ***
${LINK_TASK_1}       E2E-LINK-SESS-001
${LINK_TASK_2}       E2E-LINK-DOC-001
${LINK_TASK_3}       E2E-LINK-MULTI-001
${LINK_TASK_4}       E2E-LINK-IDEM-001

*** Keywords ***
Setup Task Linking Suite
    [Documentation]    Create tasks for linking tests, open dashboard.
    Create API Session
    Create Test Task    ${LINK_TASK_1}    Testing > Linking > Session > Dialog    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${LINK_TASK_2}    Testing > Linking > Document > Dialog    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${LINK_TASK_3}    Testing > Linking > Multi > Sessions    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${LINK_TASK_4}    Testing > Linking > Idempotent > Doc    task_type=feature    workspace_id=WS-9147535A
    Suite Setup Open Dashboard

Teardown Task Linking Suite
    [Documentation]    Clean up and close browser.
    Suite Teardown Close Browser
    Cleanup Test Task    ${LINK_TASK_1}
    Cleanup Test Task    ${LINK_TASK_2}
    Cleanup Test Task    ${LINK_TASK_3}
    Cleanup Test Task    ${LINK_TASK_4}

Setup Linking Test
    [Documentation]    SPA navigation to tasks view — reset detail state.
    Navigate To Tab    sessions
    Sleep    500ms    reason=Reset view state
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=15s
    Fill Text    ${TASKS_SEARCH} input    ${EMPTY}
    Sleep    500ms    reason=Wait for search clear

Open Task Detail For
    [Documentation]    Search for task and open its detail panel.
    [Arguments]    ${task_id}
    Fill Text    ${TASKS_SEARCH} input    ${task_id}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}

*** Test Cases ***
Link Session Button Opens Dialog
    [Documentation]    Clicking "Link Session" in task detail opens session picker.
    ...                FEAT-011: Session picker dialog with searchable list.
    [Tags]    e2e    linking    session-dialog    feat-011
    Open Task Detail For    ${LINK_TASK_1}
    # Click Link Session button — use forced click (Vuetify overlay intercepts)
    Click Element Forced    ${TASK_LINK_SESSION_BTN}
    Sleep    3s    reason=Wait for dialog + API fetch
    # Dialog should be visible
    Element Should Be Visible With Backoff    ${LINK_SESSION_DIALOG}
    Take Evidence Screenshot    link-session-dialog-open
    # Close dialog via forced click
    Click Element Forced    ${LINK_SESSION_CLOSE_BTN}

Link Document Button Opens Dialog
    [Documentation]    Clicking "Link Document" in task detail opens document browser.
    ...                FEAT-012: File tree browser with multi-select.
    [Tags]    e2e    linking    document-dialog    feat-012
    Open Task Detail For    ${LINK_TASK_2}
    # Click Link Document button — use forced click (Vuetify overlay intercepts)
    Click Element Forced    ${TASK_LINK_DOCUMENT_BTN}
    Sleep    3s    reason=Wait for dialog + API fetch
    # Dialog should be visible
    Element Should Be Visible With Backoff    ${LINK_DOCUMENT_DIALOG}
    Take Evidence Screenshot    link-document-dialog-open
    # Close dialog via forced click
    Click Element Forced    ${LINK_DOCUMENT_CANCEL_BTN}

Session Link Persists After Refresh
    [Documentation]    After linking a session via API, it persists across refresh.
    [Tags]    e2e    linking    persistence
    # Link session via API
    ${response}=    API POST    /tasks/${LINK_TASK_3}/sessions/SESSION-E2E-PERSIST-TEST
    Log    Link session: ${response.status_code}
    # Refresh and verify
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh
    Open Task Detail For    ${LINK_TASK_3}
    ${detail_text}=    Get Text    ${TASK_DETAIL}
    Should Contain    ${detail_text}    SESSION-E2E-PERSIST-TEST    msg=Linked session should persist after refresh

Document Link Idempotency
    [Documentation]    Linking same document twice doesn't create duplicates.
    [Tags]    e2e    linking    idempotency
    # Link same document twice via API
    ${payload}=    Create Dictionary    document_path=docs/RULES-DIRECTIVES.md
    ${resp1}=    API POST    /tasks/${LINK_TASK_4}/documents    ${payload}
    ${resp2}=    API POST    /tasks/${LINK_TASK_4}/documents    ${payload}
    # Get documents and check for duplicates
    ${response}=    API GET    /tasks/${LINK_TASK_4}/documents
    ${json}=    Set Variable    ${response.json()}
    ${docs}=    Get From Dictionary    ${json}    documents
    ${count}=    Get Length    ${docs}
    # Should have at most 1 entry for the same document
    Should Be True    ${count} <= 1    msg=Document link should be idempotent (got ${count} entries)
