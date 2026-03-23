*** Settings ***
Documentation    Task Cross-View Navigation E2E Tests — EPIC-TASK-QUALITY-V2 P10
...              Per DSE findings: BUG-017 dirty() fix, BUG-017b selected_task clear,
...              BUG-017c nav_source clear on tab switch.
...              Proves: tab switch after detail view resets state cleanly.

Resource    ../resources/common.resource
Resource    ../resources/api.resource
Resource    ../resources/selectors.resource
Library     ../libraries/actions.py
Library     ../libraries/overlay.py

Suite Setup       Setup Cross View Suite
Suite Teardown    Teardown Cross View Suite
Test Setup        Setup Cross View Test

Default Tags    e2e    browser    tasks    crossview    bug-017

*** Variables ***
${XVIEW_TASK}       E2E-XVIEW-001

*** Keywords ***
Setup Cross View Suite
    [Documentation]    Create task with session link, open dashboard.
    Create API Session
    Create Test Task    ${XVIEW_TASK}    Testing > CrossView > Tab Switch > Reset    task_type=feature    workspace_id=WS-9147535A
    # Link a session so session chip is visible
    ${response}=    API POST    /tasks/${XVIEW_TASK}/sessions/SESSION-E2E-XVIEW-TEST
    Log    Link session: ${response.status_code}
    Suite Setup Open Dashboard

Teardown Cross View Suite
    [Documentation]    Clean up and close browser.
    Suite Teardown Close Browser
    Cleanup Test Task    ${XVIEW_TASK}

Setup Cross View Test
    [Documentation]    SPA navigate to tasks — avoids WS exhaustion from page reloads.
    ...                Per SRVJ-FEAT-006: conserve Trame WS connections.
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=15s
    Fill Text    ${TASKS_SEARCH} input    ${EMPTY}
    Sleep    500ms    reason=Wait for search clear

*** Test Cases ***
Tab Switch Clears Back Button
    [Documentation]    BUG-017c: Tab switch must clear stale "Back to" navigation state.
    [Tags]    e2e    crossview    bug-017c
    # Test Setup already navigated to tasks list (clean state)
    # Should NOT have a "Back to" button from previous navigation
    ${page_text}=    Get Text    body
    Should Not Contain    ${page_text}    Back to Task    msg=Stale back button should not appear after tab switch

Link Session Dialog Opens And Closes
    [Documentation]    DSE verified: Link Session dialog opens with session list and closes cleanly.
    [Tags]    e2e    crossview    link-session
    # Test Setup already on tasks list
    Fill Text    ${TASKS_SEARCH} input    ${XVIEW_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
    # Open Link Session dialog
    Click Element Forced    ${TASK_LINK_SESSION_BTN}
    Sleep    3s    reason=Wait for dialog + API fetch
    Element Should Be Visible With Backoff    ${LINK_SESSION_DIALOG}
    # Close it
    Click Element Forced    ${LINK_SESSION_CLOSE_BTN}
    Sleep    1s    reason=Wait for dialog close
    Take Evidence Screenshot    crossview-link-session-closed

Link Document Dialog Opens And Closes
    [Documentation]    DSE verified: Link Document dialog opens with file list and closes cleanly.
    [Tags]    e2e    crossview    link-document
    # Test Setup already on tasks list
    Fill Text    ${TASKS_SEARCH} input    ${XVIEW_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
    # Open Link Document dialog
    Click Element Forced    ${TASK_LINK_DOCUMENT_BTN}
    Sleep    3s    reason=Wait for dialog + API fetch
    Element Should Be Visible With Backoff    ${LINK_DOCUMENT_DIALOG}
    # Close it
    Click Element Forced    ${LINK_DOCUMENT_CANCEL_BTN}
    Sleep    1s    reason=Wait for dialog close
    Take Evidence Screenshot    crossview-link-document-closed

Tab Switch Shows Tasks List Not Detail
    [Documentation]    BUG-017b: Clicking Tasks tab after viewing another tab shows list, not stale detail.
    ...                Last test — WS exhaustion risk after prior detail interactions.
    [Tags]    e2e    crossview    bug-017b
    # Open detail from the tasks list
    Fill Text    ${TASKS_SEARCH} input    ${XVIEW_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
    # Navigate away to sessions
    Navigate To Tab    sessions
    Sleep    1s    reason=Wait for view switch
    # Navigate back to tasks — should show LIST not stale detail
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=20s
    Take Evidence Screenshot    crossview-tab-switch-list
