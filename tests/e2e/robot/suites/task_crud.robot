*** Settings ***
Documentation    Task CRUD E2E Tests — EPIC-TASK-QUALITY-V2 Phase 9
...              Per TEST-E2E-01-v1: Tier 3 CRUD interaction verification.
...              Proves: API-created tasks appear in dashboard, detail panel works.

Resource    ../resources/common.resource
Resource    ../resources/api.resource
Resource    ../resources/selectors.resource
Library     ../libraries/actions.py
Library     ../libraries/overlay.py

Suite Setup       Setup Task CRUD Suite
Suite Teardown    Teardown Task CRUD Suite
Test Setup        Setup CRUD Test

Default Tags    e2e    browser    tasks    crud

*** Variables ***
${CRUD_CREATE_TASK}     E2E-CRUD-CREATE-001
${CRUD_DETAIL_TASK}     E2E-CRUD-DETAIL-001
${CRUD_UPDATE_TASK}     E2E-CRUD-UPDATE-001
${CRUD_DELETE_TASK}     E2E-CRUD-DELETE-001

*** Keywords ***
Setup Task CRUD Suite
    [Documentation]    Create API session + test tasks, open dashboard.
    Create API Session
    Create Test Task    ${CRUD_CREATE_TASK}    Testing > CRUD > Create > Visible    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${CRUD_DETAIL_TASK}    Testing > CRUD > Detail > Panel    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${CRUD_UPDATE_TASK}    Testing > CRUD > Update > Status    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${CRUD_DELETE_TASK}    Testing > CRUD > Delete > Confirm    task_type=feature    workspace_id=WS-9147535A
    Suite Setup Open Dashboard

Teardown Task CRUD Suite
    [Documentation]    Clean up test data and close browser.
    Suite Teardown Close Browser
    Cleanup Test Task    ${CRUD_CREATE_TASK}
    Cleanup Test Task    ${CRUD_DETAIL_TASK}
    Cleanup Test Task    ${CRUD_UPDATE_TASK}
    Cleanup Test Task    ${CRUD_DELETE_TASK}

Setup CRUD Test
    [Documentation]    SPA navigation to tasks view.
    ...                Per SRVJ-FEAT-006: conserve Trame WS connections.
    # Navigate away and back to reset any open detail panel
    Navigate To Tab    sessions
    Sleep    500ms    reason=Reset view state
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=15s
    Fill Text    ${TASKS_SEARCH} input    ${EMPTY}
    Sleep    500ms    reason=Wait for search clear

*** Test Cases ***
API Created Task Appears In Dashboard
    [Documentation]    Task created via POST /tasks appears in table after refresh.
    [Tags]    e2e    crud    create
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh
    Fill Text    ${TASKS_SEARCH} input    ${CRUD_CREATE_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    ${table_text}=    Get Text    ${TASKS_TABLE_BODY}
    Should Contain    ${table_text}    ${CRUD_CREATE_TASK}

Task Detail Panel Opens On Row Click
    [Documentation]    Clicking a task row opens the detail panel.
    [Tags]    e2e    crud    read
    Fill Text    ${TASKS_SEARCH} input    ${CRUD_DETAIL_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
    Take Evidence Screenshot    crud-detail-panel

Task Status Updates Via API Reflect In UI
    [Documentation]    PUT status change appears after refresh.
    [Tags]    e2e    crud    update
    # Update via API
    ${payload}=    Create Dictionary    status=IN_PROGRESS
    API PUT    /tasks/${CRUD_UPDATE_TASK}    ${payload}
    # Refresh and verify
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh
    Fill Text    ${TASKS_SEARCH} input    ${CRUD_UPDATE_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    ${table_text}=    Get Text    ${TASKS_TABLE_BODY}
    Should Contain    ${table_text}    IN_PROGRESS

Delete Task Removes From Table
    [Documentation]    DELETE /tasks/{id} removes task from dashboard.
    [Tags]    e2e    crud    delete
    # Delete via API
    API DELETE    /tasks/${CRUD_DELETE_TASK}
    # Refresh and verify gone
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh
    Fill Text    ${TASKS_SEARCH} input    ${CRUD_DELETE_TASK}
    Sleep    1s    reason=Wait for search filter
    ${table_text}=    Get Text    ${TASKS_TABLE_BODY}
    Should Not Contain    ${table_text}    ${CRUD_DELETE_TASK}
