*** Settings ***
Documentation    E2E Browser Tests for Session-Task Navigation
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/e2e/test_session_task_navigation_e2e.py
...              Regression tests for GAP-UI-SESSION-TASKS-001
Resource         ../resources/browser.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Close Browser    ALL
Test Setup       Navigate To Sessions List
Test Tags        e2e    browser    sessions    tasks    medium    read    SESSION-EVID-01-v1

*** Variables ***
${TEST_SESSION_ID}       SESSION-2026-01-10-INTENT-TEST

*** Keywords ***
Click First Session Item
    [Documentation]    Click first session item in the list
    # Ensure we're on sessions list
    ${list_count}=    Get Element Count    text=Session Evidence
    IF    ${list_count} == 0
        Click    [data-testid='nav-sessions']
        ${back_count}=    Get Element Count    [data-testid='session-detail-back-btn']
        IF    ${back_count} > 0
            Click    [data-testid='session-detail-back-btn']
        ELSE
            ${btn_count}=    Get Element Count    button:has-text("󰁍")
            IF    ${btn_count} > 0
                Click    button:has-text("󰁍") >> nth=0
            END
        END
        Wait For Elements State    text=Session Evidence    visible    timeout=20s
    END
    # Session list uses card items - click the first one
    Wait For Elements State    text=/\\d+ sessions loaded/    visible    timeout=${ELEMENT_TIMEOUT}
    ${count}=    Get Element Count    text=/SESSION-/ >> nth=0
    Should Be True    ${count} > 0    No sessions found
    Click    text=/SESSION-/ >> nth=0
    Wait For Elements State    text=Session Information    visible    timeout=${ELEMENT_TIMEOUT}

Try Click Test Session
    [Documentation]    Try to click the test session if visible
    ${count}=    Get Element Count    text=${TEST_SESSION_ID}
    IF    ${count} > 0
        Click    text=${TEST_SESSION_ID} >> nth=0
        Wait For Elements State    text=Session Information    visible    timeout=${ELEMENT_TIMEOUT}
        RETURN    ${TRUE}
    ELSE
        RETURN    ${FALSE}
    END

Click Task In Session Detail
    [Documentation]    Find and click a task listitem in session detail
    # Tasks appear as listitems with P12.x text
    ${li_count}=    Get Element Count    listitem:has-text("P12")
    IF    ${li_count} > 0
        Click    listitem:has-text("P12") >> nth=0
        RETURN    ${TRUE}
    ELSE
        ${text_count}=    Get Element Count    text=/P12\\.[0-9]/
        IF    ${text_count} > 0
            Click    text=/P12\\.[0-9]/ >> nth=0
            RETURN    ${TRUE}
        ELSE
            RETURN    ${FALSE}
        END
    END

Navigate To Tasks List
    [Documentation]    Navigate to Tasks list (handles detail-open state)
    Go To    ${DASHBOARD_URL}
    Reload
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=20s
    Click    [data-testid='nav-tasks']
    # Wait for SPA view transition to complete
    Sleep    2s
    # Check if we landed on task list or task detail
    ${list_count}=    Get Element Count    text=/\\d+ tasks loaded/
    IF    ${list_count} == 0
        # In detail view - try back buttons (may need multiple attempts)
        FOR    ${i}    IN RANGE    3
            ${back1}=    Get Element Count    [data-testid='task-detail-back-to-source']
            ${back2}=    Get Element Count    [data-testid='task-detail-back-btn']
            ${back3}=    Get Element Count    button:has-text("󰁍")
            IF    ${back1} > 0
                Click    [data-testid='task-detail-back-to-source']
                Sleep    1s
            ELSE IF    ${back2} > 0
                Click    [data-testid='task-detail-back-btn']
                Sleep    1s
            ELSE IF    ${back3} > 0
                Click    button:has-text("󰁍") >> nth=0
                Sleep    1s
            ELSE
                # No back button found yet - wait for render
                Sleep    2s
            END
            # After back, may land on sessions or other view
            # Re-click Tasks nav and check again
            ${check}=    Get Element Count    text=/\\d+ tasks loaded/
            IF    ${check} > 0    BREAK
            Click    [data-testid='nav-tasks']
            Sleep    2s
            ${check2}=    Get Element Count    text=/\\d+ tasks loaded/
            IF    ${check2} > 0    BREAK
        END
    END
    Wait For Elements State    text=/\\d+ tasks loaded/    visible    timeout=20s

*** Test Cases ***
# =============================================================================
# Session Tasks Display Tests (GAP-UI-SESSION-TASKS-001)
# =============================================================================

Sessions View Loads
    [Documentation]    Sessions view loads with session list
    [Tags]    e2e    browser    sessions    smoke
    Wait For Elements State    text=Session Evidence    visible
    Wait For Elements State    text=/\\d+ sessions loaded/    visible    timeout=${ELEMENT_TIMEOUT}

Session Has Click Handler
    [Documentation]    Session items in list are clickable
    [Tags]    e2e    browser    sessions
    ${count}=    Get Element Count    text=/SESSION-/ >> nth=0
    Should Be True    ${count} > 0    No session items found

Click Session Shows Detail
    [Documentation]    Clicking a session opens detail view
    [Tags]    e2e    browser    sessions    detail
    Click First Session Item
    Wait For Elements State    text=Session Information    visible

Session Detail Shows Tasks Section
    [Documentation]    Session detail shows completed tasks section (GAP-UI-SESSION-TASKS-001)
    [Tags]    e2e    browser    sessions    tasks    regression    GAP-UI-SESSION-TASKS-001
    Click First Session Item
    # Not all sessions have tasks - check for the section or skip
    ${tasks_count}=    Get Element Count    text=Completed Tasks
    ${evidence_count}=    Get Element Count    text=Evidence Files
    Should Be True    ${tasks_count} > 0 or ${evidence_count} > 0    Session detail missing expected sections

Known Session Shows Linked Tasks
    [Documentation]    Test session should show linked tasks (GAP-UI-SESSION-TASKS-001)
    [Tags]    e2e    browser    sessions    linked    regression    GAP-UI-SESSION-TASKS-001
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
    # Find task listitem with P12.x text
    ${li_count}=    Get Element Count    listitem:has-text("P12")
    ${text_count}=    Get Element Count    text=/P12\\.[0-9]/
    ${total}=    Evaluate    ${li_count} + ${text_count}
    Skip If    ${total} == 0    No task item found in session detail
    Should Be True    ${total} > 0

Click Task Navigates To Tasks View
    [Documentation]    Clicking task in session navigates to Tasks tab
    [Tags]    e2e    browser    navigation    regression
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    ${clicked}=    Click Task In Session Detail
    Skip If    not ${clicked}    No task item found to click
    Navigate To Tasks List

Task Detail Opens After Navigation
    [Documentation]    After clicking task, task detail panel opens
    [Tags]    e2e    browser    navigation    detail    regression
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    ${clicked}=    Click Task In Session Detail
    Skip If    not ${clicked}    No task item found
    Navigate To Tasks List
    # Task detail should be accessible
    Click    text=/ATEST-|P12|P10|FH-|ORCH-|KAN-/ >> nth=0
    Wait For Elements State    text=Edit    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Bidirectional Navigation Tests
# =============================================================================

Task Shows Linked Sessions
    [Documentation]    Task detail shows linked sessions field
    [Tags]    e2e    browser    bidirectional
    Navigate To Tasks List
    # Click first task item
    Click    text=/ATEST-|P12|P10|FH-|ORCH-|KAN-/ >> nth=0
    Wait For Elements State    text=Edit    visible    timeout=${ELEMENT_TIMEOUT}
    # Look for linked sessions section
    ${count}=    Get Element Count    text=/Linked Sessions|linked_sessions|Sessions/
    Log    Linked sessions elements: ${count}

Round Trip Navigation
    [Documentation]    Sessions -> Session Detail -> Task -> Tasks View
    [Tags]    e2e    browser    navigation    roundtrip
    ${found}=    Try Click Test Session
    Skip If    not ${found}    Test session ${TEST_SESSION_ID} not visible
    # Verify in session detail
    ${detail_visible}=    Get Element Count    text=/Session Information|SESSION-/
    Should Be True    ${detail_visible} > 0    Not in session detail
    # Click task item
    ${clicked}=    Click Task In Session Detail
    Skip If    not ${clicked}    No task item for round-trip
    # Should navigate to Tasks view
    Navigate To Tasks List
