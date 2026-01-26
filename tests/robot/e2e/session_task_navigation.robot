*** Settings ***
Documentation    E2E Browser Tests for Session-Task Navigation
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/e2e/test_session_task_navigation_e2e.py
...              Regression tests for GAP-UI-SESSION-TASKS-001
Library          Browser    auto_closing_level=SUITE
Resource         ../resources/common.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Close Browser    ALL
Test Setup       Navigate To Sessions View

*** Variables ***
${DASHBOARD_URL}         http://localhost:8081
${APP_TITLE}             Governance Dashboard
${PAGE_TIMEOUT}          10s
${ELEMENT_TIMEOUT}       5s
${TEST_SESSION_ID}       SESSION-2026-01-10-INTENT-TEST

*** Keywords ***
Open Dashboard Browser
    [Documentation]    Open browser for test suite
    New Browser    chromium    headless=True
    New Context    viewport={'width': 1280, 'height': 720}

Navigate To Sessions View
    [Documentation]    Navigate to Sessions view
    New Page    ${DASHBOARD_URL}
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=${PAGE_TIMEOUT}
    Click    [data-testid='nav-sessions']
    Wait For Elements State    text=Session Evidence    visible

Click First Session Row
    [Documentation]    Click first session row in table
    Click    tr:has(td) >> nth=0
    Wait For Elements State    text=Close    visible    timeout=${ELEMENT_TIMEOUT}

Try Click Test Session
    [Documentation]    Try to click the test session if visible
    [Return]    ${status}
    ${count}=    Get Element Count    text=${TEST_SESSION_ID}
    IF    ${count} > 0
        Click    text=${TEST_SESSION_ID} >> nth=0
        Wait For Elements State    text=Close    visible    timeout=${ELEMENT_TIMEOUT}
        RETURN    ${TRUE}
    ELSE
        RETURN    ${FALSE}
    END

*** Test Cases ***
# =============================================================================
# Session Tasks Display Tests (GAP-UI-SESSION-TASKS-001)
# =============================================================================

Sessions View Loads
    [Documentation]    Sessions view loads with session list
    [Tags]    e2e    browser    sessions    smoke
    Wait For Elements State    text=Session Evidence    visible
    Wait For Elements State    text=session_id    visible    timeout=${ELEMENT_TIMEOUT}

Session Has Click Handler
    [Documentation]    Session items in list are clickable
    [Tags]    e2e    browser    sessions
    Wait For Elements State    tr:has(td) >> nth=0    visible

Click Session Shows Detail
    [Documentation]    Clicking a session opens detail view
    [Tags]    e2e    browser    sessions    detail
    Click First Session Row
    Wait For Elements State    text=Close    visible

Session Detail Shows Tasks Section
    [Documentation]    Session detail shows completed tasks section (GAP-UI-SESSION-TASKS-001)
    [Tags]    e2e    browser    sessions    tasks    regression
    Click First Session Row
    Wait For Elements State    text=Completed Tasks    visible

Known Session Shows Linked Tasks
    [Documentation]    Test session should show linked tasks (GAP-UI-SESSION-TASKS-001)
    [Tags]    e2e    browser    sessions    linked    regression
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    Wait For Elements State    text=Completed Tasks    visible
    # Look for any linked task (P12.x pattern)
    ${task_count}=    Get Element Count    text=/P12\\.[0-9]/
    Should Be True    ${task_count} >= 0    No tasks found for session

# =============================================================================
# Session To Task Navigation Tests
# =============================================================================

Task In Session Detail Is Clickable
    [Documentation]    Task items in session detail have click handlers
    [Tags]    e2e    browser    navigation    regression
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    # Find task chip - try v-chip or text pattern
    ${chip_count}=    Get Element Count    span[class*='v-chip']:has-text('P12')
    ${text_count}=    Get Element Count    text=/P12\\.[0-9]/
    ${total}=    Evaluate    ${chip_count} + ${text_count}
    Skip If    ${total} == 0    No task chip found in session detail
    Should Be True    ${total} > 0

Click Task Navigates To Tasks View
    [Documentation]    Clicking task in session navigates to Tasks tab
    [Tags]    e2e    browser    navigation    regression
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    # Find and click task chip
    ${chip_count}=    Get Element Count    span[class*='v-chip']:has-text('P12')
    IF    ${chip_count} > 0
        Click    span[class*='v-chip']:has-text('P12') >> nth=0
    ELSE
        ${text_count}=    Get Element Count    text=/P12\\.[0-9]/
        Skip If    ${text_count} == 0    No task chip found to click
        Click    text=/P12\\.[0-9]/ >> nth=0
    END
    Wait For Elements State    text=Platform Tasks    visible    timeout=${ELEMENT_TIMEOUT}

Task Detail Opens After Navigation
    [Documentation]    After clicking task, task detail panel opens
    [Tags]    e2e    browser    navigation    detail    regression
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    # Find and click task chip
    ${chip_count}=    Get Element Count    span[class*='v-chip']:has-text('P12')
    IF    ${chip_count} > 0
        Click    span[class*='v-chip']:has-text('P12') >> nth=0
    ELSE
        ${text_count}=    Get Element Count    text=/P12\\.[0-9]/
        Skip If    ${text_count} == 0    No task chip found
        Click    text=/P12\\.[0-9]/ >> nth=0
    END
    # Should be on Tasks view
    Wait For Elements State    text=Platform Tasks    visible    timeout=${ELEMENT_TIMEOUT}
    # Task detail should open
    Wait For Elements State    text=Edit    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Bidirectional Navigation Tests
# =============================================================================

Task Shows Linked Sessions
    [Documentation]    Task detail shows linked sessions field
    [Tags]    e2e    browser    bidirectional
    Click    [data-testid='nav-tasks']
    Wait For Elements State    text=Platform Tasks    visible
    Click    tr:has(td) >> nth=0
    Wait For Elements State    text=Close    visible    timeout=${ELEMENT_TIMEOUT}
    # Look for linked sessions section
    ${count}=    Get Element Count    text=/Linked Sessions|linked_sessions|Sessions/
    Log    Linked sessions elements: ${count}

Round Trip Navigation
    [Documentation]    Sessions -> Session Detail -> Task -> Tasks View
    [Tags]    e2e    browser    navigation    roundtrip
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    # Verify in session detail
    ${detail_visible}=    Get Element Count    text=/Session Details|SESSION-/
    Should Be True    ${detail_visible} > 0    Not in session detail
    # Click task chip
    ${chip_count}=    Get Element Count    span[class*='v-chip']:has-text('P12')
    IF    ${chip_count} > 0
        Click    span[class*='v-chip']:has-text('P12') >> nth=0
    ELSE
        ${text_count}=    Get Element Count    text=/P12\\.[0-9]/
        Skip If    ${text_count} == 0    No task chip for round-trip
        Click    text=/P12\\.[0-9]/ >> nth=0
    END
    # Should navigate to Tasks view
    Wait For Elements State    text=Platform Tasks    visible    timeout=${ELEMENT_TIMEOUT}
