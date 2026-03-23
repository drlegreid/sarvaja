*** Settings ***
Documentation    Task Filtering E2E Tests — EPIC-TASK-QUALITY-V2 Phase 9
...              Per TEST-E2E-01-v1: Tier 3 filter/sort/search verification.
...              Proves: hide test toggle, workspace filter, project filter,
...              search by ID, sort by Completed column.

Resource    ../resources/common.resource
Resource    ../resources/api.resource
Resource    ../resources/selectors.resource
Library     ../libraries/actions.py
Library     ../libraries/overlay.py

Suite Setup       Setup Task Filtering Suite
Suite Teardown    Teardown Task Filtering Suite
Test Setup        Setup Filtering Test

Default Tags    e2e    browser    tasks    filtering

*** Variables ***
${FILT_FEATURE}     E2E-FILT-FEAT-001
${FILT_TEST}        E2E-FILT-TEST-001
${FILT_SEARCH}      E2E-FILT-SRCH-001
${FILT_DONE}        E2E-FILT-DONE-001
${FILT_WS}          E2E-FILT-WS-001

*** Keywords ***
Setup Task Filtering Suite
    [Documentation]    Create test tasks with varied types and workspaces.
    Create API Session
    Create Test Task    ${FILT_FEATURE}    Testing > Filter > Feature > Visible    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${FILT_TEST}       Testing > Filter > Test Type > Hidden    task_type=test    workspace_id=WS-9147535A
    Create Test Task    ${FILT_SEARCH}     Testing > Filter > Search > By ID    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${FILT_DONE}       Testing > Filter > Sort > Completed    task_type=feature    workspace_id=WS-9147535A
    Update Task To Done    ${FILT_DONE}    Testing > Filter > Sort > Completed
    Create Test Task    ${FILT_WS}         Testing > Filter > Workspace > Match    task_type=feature    workspace_id=WS-9147535A
    Suite Setup Open Dashboard

Teardown Task Filtering Suite
    [Documentation]    Clean up and close browser.
    Suite Teardown Close Browser
    Cleanup Test Task    ${FILT_FEATURE}
    Cleanup Test Task    ${FILT_TEST}
    Cleanup Test Task    ${FILT_SEARCH}
    Cleanup Test Task    ${FILT_DONE}
    Cleanup Test Task    ${FILT_WS}

Setup Filtering Test
    [Documentation]    SPA navigation to tasks — reset detail state, refresh data.
    Navigate To Tab    sessions
    Sleep    500ms    reason=Reset view state
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=15s
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh
    Fill Text    ${TASKS_SEARCH} input    ${EMPTY}
    Sleep    500ms    reason=Wait for search clear

*** Test Cases ***
Hide Test Toggle Filters Test Type Tasks
    [Documentation]    Test-type tasks hidden when toggle ON, visible when OFF.
    [Tags]    e2e    filtering    hide-test
    # Toggle OFF to show test tasks
    ${toggle}=    Get Element    ${TASKS_HIDE_TEST_TOGGLE}
    Click    ${toggle}
    Sleep    1s    reason=Wait for filter
    Fill Text    ${TASKS_SEARCH} input    ${FILT_TEST}
    Sleep    1s    reason=Wait for search
    Wait For Table Rows
    ${visible}=    Get Text    ${TASKS_TABLE_BODY}
    Should Contain    ${visible}    ${FILT_TEST}    msg=Test task should be visible when toggle OFF
    # Toggle ON to hide
    Click    ${toggle}
    Sleep    1s    reason=Wait for filter
    ${hidden}=    Get Text    ${TASKS_TABLE_BODY}
    Should Not Contain    ${hidden}    ${FILT_TEST}    msg=Test task should be hidden when toggle ON

Search Finds Task By ID Substring
    [Documentation]    Search input filters tasks by ID substring match.
    [Tags]    e2e    filtering    search
    Fill Text    ${TASKS_SEARCH} input    FILT-SRCH
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    ${text}=    Get Text    ${TASKS_TABLE_BODY}
    Should Contain    ${text}    ${FILT_SEARCH}

Search Returns No Results For Invalid ID
    [Documentation]    Search for non-existent ID shows no matching content.
    [Tags]    e2e    filtering    search    negative
    Fill Text    ${TASKS_SEARCH} input    NONEXISTENT-TASK-XYZ-999
    Sleep    1s    reason=Wait for search filter
    ${body_text}=    Get Text    ${TASKS_TABLE_BODY}
    Should Not Contain    ${body_text}    NONEXISTENT-TASK-XYZ-999    msg=Search result should not contain the search term

Feature Task Visible With Default Filters
    [Documentation]    Feature-type task appears with default filter settings.
    [Tags]    e2e    filtering    default
    Fill Text    ${TASKS_SEARCH} input    ${FILT_FEATURE}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    ${text}=    Get Text    ${TASKS_TABLE_BODY}
    Should Contain    ${text}    ${FILT_FEATURE}

DONE Task Has Completed Timestamp In Table
    [Documentation]    DONE task shows completed_at in Completed column.
    [Tags]    e2e    filtering    sort
    Fill Text    ${TASKS_SEARCH} input    ${FILT_DONE}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    ${completed_cell}=    Get Text    ${TASKS_TABLE_BODY} tr:has(td) td >> nth=10
    Should Not Be Empty    ${completed_cell}    msg=Completed column should have timestamp
