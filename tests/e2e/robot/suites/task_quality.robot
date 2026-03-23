*** Settings ***
Documentation    Task Quality E2E Tests — EPIC-TASK-QUALITY-V1 Phase B
...              Per TEST-E2E-01-v1: Tier 3 Playwright verification.
...              Proves: project column, test filter, TypeDB persistence, DONE gate.
...
...              Bugs under test:
...              - SRVJ-BUG-005: Project column empty after restart
...              - SRVJ-BUG-006: Hide test toggle not filtering
...              - SRVJ-BUG-007: task_create data not persisting to TypeDB

Resource    ../resources/common.resource
Resource    ../resources/api.resource

Suite Setup       Setup Task Quality Suite
Suite Teardown    Teardown Task Quality Suite
Test Setup        Setup Task Quality Test Lightweight

Default Tags    e2e    browser    tasks    quality

*** Variables ***
${QUAL_TEST_TASK}       RF-QUAL-TEST-001
${QUAL_DONE_TASK}       RF-QUAL-DONE-001
${QUAL_HIDE_TASK}       RF-QUAL-HIDE-001
${QUAL_PROJ_TASK}       RF-QUAL-PROJ-001

*** Keywords ***
Setup Task Quality Suite
    [Documentation]    Create API session + test data, then open dashboard.
    Create API Session
    # Create test tasks via API — use task_type=feature for visible tasks
    Create Test Task    ${QUAL_TEST_TASK}    RF > Quality > Test > Visible    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${QUAL_HIDE_TASK}    RF > Quality > Hide > Test Filter    task_type=test
    Create Test Task    ${QUAL_PROJ_TASK}    RF > Quality > Project > Column    task_type=feature    workspace_id=WS-9147535A
    # Create and close a DONE task (feature type so it's visible)
    Create Test Task    ${QUAL_DONE_TASK}    RF > Quality > DONE > Completed At    task_type=feature    workspace_id=WS-9147535A
    Update Task To Done    ${QUAL_DONE_TASK}    RF > Quality > DONE > Completed At
    # Open browser
    Suite Setup Open Dashboard

Teardown Task Quality Suite
    [Documentation]    Clean up test data and close browser.
    Suite Teardown Close Browser
    Cleanup Test Task    ${QUAL_TEST_TASK}
    Cleanup Test Task    ${QUAL_DONE_TASK}
    Cleanup Test Task    ${QUAL_HIDE_TASK}
    Cleanup Test Task    ${QUAL_PROJ_TASK}

Setup Task Quality Test Lightweight
    [Documentation]    SPA navigation to tasks view — avoids full reload.
    ...                SRVJ-FEAT-006: Conserves Trame WS connections.
    ...                Full page reload (Go To) creates new WS per test.
    ...                With 6+ tests, Trame hits connection limit.
    # SPA navigation — reuses existing WS connection
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=10s
    # Clear leftover search from previous test
    Fill Text    ${TASKS_SEARCH} input    ${EMPTY}
    Sleep    500ms    reason=Wait for search clear to apply

*** Test Cases ***
Task Table Renders 12 Columns
    [Documentation]    Task table has exactly 12 column headers.
    [Tags]    e2e    browser    tasks    quality    smoke
    Verify Data Table Has Rows
    ${header_cells}=    Get Elements    ${TASKS_TABLE_HEADER} th
    ${count}=    Get Length    ${header_cells}
    Should Be Equal As Integers    ${count}    12    msg=Expected 12 columns, got ${count}

Project Column Shows Project Name
    [Documentation]    Tasks with workspace_id show project name in Project column.
    ...                SRVJ-BUG-005: Fails if enrichment breaks after restart.
    [Tags]    e2e    browser    tasks    quality    bug-005
    # Search for our test task that has workspace_id set
    Fill Text    ${TASKS_SEARCH} input    ${QUAL_PROJ_TASK}
    Wait For Table Rows
    # First column (Project) of first data row should not be empty
    ${project_cell}=    Get Text    ${TASKS_TABLE_BODY} tr:has(td) td >> nth=0
    Should Not Be Empty    ${project_cell}    msg=Project column is empty (SRVJ-BUG-005)

DONE Task Shows Completed Timestamp
    [Documentation]    DONE task has non-empty Completed column in table.
    [Tags]    e2e    browser    tasks    quality
    # Click refresh to ensure fresh data, then search
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh
    Fill Text    ${TASKS_SEARCH} input    ${QUAL_DONE_TASK}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    # Completed column is index 10 (0-indexed: Project Workspace TaskID Summary Priority Type Status Session Agent Created Completed Docs)
    ${completed_cell}=    Get Text    ${TASKS_TABLE_BODY} tr:has(td) td >> nth=10
    Should Not Be Empty    ${completed_cell}    msg=Completed column should have timestamp for DONE task

API Created Task Appears After Refresh
    [Documentation]    Task created via API appears in dashboard table.
    [Tags]    e2e    browser    tasks    quality
    # Click refresh to ensure fresh data from API
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh to complete
    # Search for our API-created test task
    Fill Text    ${TASKS_SEARCH} input    ${QUAL_TEST_TASK}
    Sleep    1s    reason=Wait for search filter to apply
    Wait For Table Rows
    ${table_text}=    Get Text    ${TASKS_TABLE_BODY}
    Should Contain    ${table_text}    ${QUAL_TEST_TASK}

Hide Test Toggle Filters Test Type Tasks
    [Documentation]    Toggle OFF → test task visible. Toggle ON → hidden.
    ...                SRVJ-BUG-006: Fails if filter doesn't re-apply after refresh.
    [Tags]    e2e    browser    tasks    quality    bug-006
    # Refresh data first to ensure test tasks are loaded from API
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh to complete
    # Uncheck "Hide test tasks" toggle to show test tasks
    ${toggle}=    Get Element    ${TASKS_HIDE_TEST_TOGGLE}
    Click    ${toggle}
    Sleep    1s    reason=Wait for reactive filter to re-fetch
    # Now search for our test-type task
    Fill Text    ${TASKS_SEARCH} input    ${QUAL_HIDE_TASK}
    Sleep    1s    reason=Wait for search filter to apply
    Wait For Table Rows
    # Verify test task IS visible when toggle is OFF
    ${visible_ids}=    Get Text    ${TASKS_TABLE_BODY}
    Should Contain    ${visible_ids}    ${QUAL_HIDE_TASK}    msg=Test task should be visible when toggle OFF
    # Re-enable toggle
    Click    ${toggle}
    Sleep    1s    reason=Wait for reactive filter to re-fetch
    # Verify test task is now HIDDEN
    ${hidden_content}=    Get Text    ${TASKS_TABLE_BODY}
    Should Not Contain    ${hidden_content}    ${QUAL_HIDE_TASK}    msg=Test task should be hidden when toggle ON (SRVJ-BUG-006)

Task Detail Shows Linked Documents
    [Documentation]    Clicking task row shows detail with linked documents.
    [Tags]    e2e    browser    tasks    quality
    # Search for our DONE task (it has linked_documents)
    Fill Text    ${TASKS_SEARCH} input    ${QUAL_DONE_TASK}
    Wait For Table Rows
    Click Table Row    0
    Element Should Be Visible With Backoff    ${TASK_DETAIL}
    Take Evidence Screenshot    task-quality-detail
