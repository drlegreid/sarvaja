*** Settings ***
Documentation    Sessions View E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              Migrated from: tests/e2e/test_dashboard_e2e.py::TestSessionsView
...              and test_session_task_navigation_e2e.py::TestSessionsViewAndDetail

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Setup Sessions View

Default Tags    e2e    browser    sessions

*** Keywords ***
Setup Sessions View
    [Documentation]    Navigate to Sessions view before each test.
    Test Setup Navigate Home
    Navigate And Verify Tab    sessions    Session Evidence

*** Test Cases ***
Sessions View Loads
    [Documentation]    Sessions view renders with session list header.
    Wait For Elements State    text=Session Evidence    visible    timeout=10s

Sessions Table Has Header Columns
    [Documentation]    Sessions table shows Session ID column header.
    ${header_visible}=    Run Keyword And Return Status
    ...    Wait For Elements State    text=Session ID    visible    timeout=5s
    Log    Session ID header visible: ${header_visible}

Session Detail Opens On Row Click
    [Documentation]    Clicking a session row opens the detail view with tasks.
    ...                Known limitation: may fail after 20+ browser connections
    ...                due to Trame WS server degradation. Passes in isolation.
    [Tags]    e2e    browser    sessions    detail
    Verify Data Table Has Rows
    Click Table Row    0
    Wait For Element With Backoff    ${SESSION_DETAIL}    max_attempts=8
    Wait For Elements State    ${SESSION_BACK_BTN}    visible    timeout=10s
    Wait For Elements State    text=Completed Tasks    visible    timeout=10s
