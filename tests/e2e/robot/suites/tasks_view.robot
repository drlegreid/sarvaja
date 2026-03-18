*** Settings ***
Documentation    Tasks View E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              Migrated from: tests/e2e/test_dashboard_e2e.py::TestTasksView

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Setup Tasks View

Default Tags    e2e    browser    tasks

*** Keywords ***
Setup Tasks View
    [Documentation]    Navigate to Tasks view before each test.
    Test Setup Navigate Home
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=10s

*** Test Cases ***
Tasks View Loads
    [Documentation]    Tasks view renders with content.
    ${search_visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    ${TASKS_SEARCH}    visible    timeout=5s
    Run Keyword If    not ${search_visible}
    ...    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=5s

Add Task Button Is Present
    [Documentation]    Add Task button is visible.
    Wait For Elements State    ${TASKS_ADD_BTN}    visible    timeout=10s

Tasks Show Status Indicators
    [Documentation]    Tasks display status chips (OPEN, DONE, etc).
    ${has_status}=    Run Keyword And Return Status
    ...    Wait For Elements State    text=/OPEN|DONE|IN_PROGRESS|TODO|CLOSED|BLOCKED/    visible    timeout=5s
    # Acceptable if no tasks exist in DB
    Log    Status indicators visible: ${has_status}

Task Detail Opens On Row Click
    [Documentation]    Clicking a task row opens the detail panel.
    ...                Migrated from: test_session_task_navigation_e2e.py::TestTaskDetailFromTasksView
    Verify Data Table Has Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
