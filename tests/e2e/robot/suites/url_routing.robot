*** Settings ***
Documentation    URL Routing E2E Tests (FEAT-008, TEST-001, TEST-002)
...              Verifies hash-based URI routing for dashboard navigation.
...              Per TEST-E2E-01-v1: Tier 3 browser verification.
...              TEST-001: Same-view entity deep link reload (SRVJ-FEAT-015)
...              TEST-002: Cross-entity hash update on session chip (SRVJ-FEAT-016)

Resource    ../resources/common.resource
Resource    ../resources/api.resource
Resource    ../resources/selectors.resource
Library     ../libraries/actions.py
Library     ../libraries/overlay.py

Suite Setup       Setup URL Routing Suite
Suite Teardown    Teardown URL Routing Suite
Test Setup        Test Setup Navigate Home

Default Tags    e2e    browser    routing    FEAT-008

*** Variables ***
${DEEPLINK_TASK_A}       E2E-DEEPLINK-A-001
${DEEPLINK_TASK_B}       E2E-DEEPLINK-B-001
${XHASH_TASK}            E2E-XHASH-001
${XHASH_SESSION_ID}      SESSION-E2E-XHASH-TEST

*** Keywords ***
Setup URL Routing Suite
    [Documentation]    Create test tasks for deep link tests, open dashboard.
    Create API Session
    api.Create Test Task    ${DEEPLINK_TASK_A}    Testing > DeepLink > TaskA > SameView    task_type=feature    workspace_id=WS-TEST-SANDBOX
    api.Create Test Task    ${DEEPLINK_TASK_B}    Testing > DeepLink > TaskB > SameView    task_type=feature    workspace_id=WS-TEST-SANDBOX
    api.Create Test Task    ${XHASH_TASK}         Testing > XHash > SessionChip > URLSync    task_type=feature    workspace_id=WS-TEST-SANDBOX
    # Link a session to xhash task for session chip test
    ${response}=    API POST    /tasks/${XHASH_TASK}/sessions/${XHASH_SESSION_ID}
    Log    Link session: ${response.status_code}
    Suite Setup Open Dashboard

Teardown URL Routing Suite
    [Documentation]    Clean up test data and close browser.
    Suite Teardown Close Browser
    api.Cleanup Test Task    ${DEEPLINK_TASK_A}
    api.Cleanup Test Task    ${DEEPLINK_TASK_B}
    api.Cleanup Test Task    ${XHASH_TASK}

*** Test Cases ***
Route Sync JS Is Loaded
    [Documentation]    The route_sync.js script should be injected and sarvaja_push_hash available.
    ${result}=    Evaluate JavaScript    ${None}    typeof window.sarvaja_push_hash
    Should Be Equal    ${result}    function

Navigate To Tasks Updates URL Hash
    [Documentation]    Clicking Tasks tab should update browser hash to include /tasks.
    Navigate To Tab    tasks
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash}    tasks

Navigate To Sessions Updates URL Hash
    [Documentation]    Clicking Sessions tab should update browser hash.
    Navigate To Tab    sessions
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash}    sessions

Navigate To Rules Updates URL Hash
    [Documentation]    Clicking Rules tab should update browser hash.
    Navigate To Tab    rules
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash}    rules

Standalone View Executive Has Simple Hash
    [Documentation]    Executive view should produce #/executive hash.
    Navigate To Tab    executive
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Be Equal    ${hash}    #/executive

Standalone View Monitor Has Simple Hash
    [Documentation]    Monitor view should produce #/monitor hash.
    Navigate To Tab    monitor
    Sleep    1s
    ${hash}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Be Equal    ${hash}    #/monitor

Direct Hash Navigation To Tasks
    [Documentation]    Setting hash directly should navigate to tasks view.
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-9147535A/tasks'
    Sleep    2s
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=10s

Direct Hash Navigation To Sessions
    [Documentation]    Setting hash directly should navigate to sessions view.
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-9147535A/sessions'
    Sleep    2s
    Wait For Elements State    [data-testid='sessions-table']    visible    timeout=10s

Direct Hash Navigation To Executive
    [Documentation]    Standalone view via hash.
    Evaluate JavaScript    ${None}    window.location.hash = '#/executive'
    Sleep    2s
    Element Should Be Visible With Backoff    text=Executive

Hash Changes On Tab Switch Sequence
    [Documentation]    Rapid tab switching updates hash each time.
    Navigate To Tab    tasks
    Sleep    1s
    ${h1}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${h1}    tasks
    Navigate To Tab    sessions
    Sleep    1s
    ${h2}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${h2}    sessions
    Navigate To Tab    rules
    Sleep    1s
    ${h3}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${h3}    rules

Same View Entity Deep Link Reloads Detail
    [Documentation]    TEST-001 / SRVJ-FEAT-015: Navigating from task A to task B via hash
    ...                (same view, no tab change) must reload the detail panel with task B.
    [Tags]    e2e    routing    deep-link    TEST-001    SRVJ-FEAT-015
    # Navigate to tasks view via hash (reliable — avoids Navigate To Tab flakiness)
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-TEST-SANDBOX/tasks'
    Sleep    2s
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=15s
    # Deep link to task A via hash
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-TEST-SANDBOX/tasks/${DEEPLINK_TASK_A}'
    Sleep    2s    reason=Wait for route_sync to fire on_route_change
    # Verify task A is loaded in detail
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
    ${detail_a}=    Get Text    ${TASK_DETAIL}
    Should Contain    ${detail_a}    ${DEEPLINK_TASK_A}    msg=Detail panel should show task A
    Take Evidence Screenshot    deeplink-task-a-loaded
    # Now deep link to task B — same view, no tab switch
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-TEST-SANDBOX/tasks/${DEEPLINK_TASK_B}'
    Sleep    2s    reason=Wait for same-view entity reload
    # Verify task B replaced task A in detail
    ${detail_b}=    Get Text    ${TASK_DETAIL}
    Should Contain    ${detail_b}    ${DEEPLINK_TASK_B}    msg=Detail panel should reload with task B
    Should Not Contain    ${detail_b}    ${DEEPLINK_TASK_A}    msg=Task A should no longer be in detail
    Take Evidence Screenshot    deeplink-task-b-reloaded

Session Chip Click Updates URL Hash
    [Documentation]    TEST-002 / SRVJ-FEAT-016: Clicking a session chip in task detail
    ...                must update the URL hash to include /sessions/{session_id}.
    [Tags]    e2e    routing    cross-entity    TEST-002    SRVJ-FEAT-016
    # Navigate to tasks via hash (reliable path)
    Evaluate JavaScript    ${None}    window.location.hash = '#/projects/WS-TEST-SANDBOX/tasks'
    Sleep    2s
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=15s
    # Search for the xhash task and open detail
    Fill Text    ${TASKS_SEARCH} input    ${XHASH_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
    # Capture hash before chip click
    ${hash_before}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash_before}    tasks    msg=Should be on tasks route before chip click
    Take Evidence Screenshot    xhash-before-chip-click
    # Click session chip — triggers cross-entity navigation
    Click    ${TASK_SESSION_CHIP} >> nth=0
    Sleep    2s    reason=Wait for cross-view navigation + hash push
    # Verify hash updated to sessions route
    ${hash_after}=    Evaluate JavaScript    ${None}    window.location.hash
    Should Contain    ${hash_after}    sessions    msg=Hash should update to sessions after chip click
    Take Evidence Screenshot    xhash-after-chip-click
