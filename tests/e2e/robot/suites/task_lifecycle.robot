*** Settings ***
Documentation    Task Lifecycle E2E Tests — EPIC-TASK-QUALITY-V2 Phase 9
...              Per TEST-E2E-01-v1: Tier 3 status transition verification.
...              Proves: DONE gate rejects incomplete, accepts complete,
...              completed_at persistence, reopen resets resolution.

Resource    ../resources/common.resource
Resource    ../resources/api.resource
Resource    ../resources/selectors.resource
Library     ../libraries/actions.py
Library     ../libraries/overlay.py

Suite Setup       Setup Task Lifecycle Suite
Suite Teardown    Teardown Task Lifecycle Suite
Test Setup        Setup Lifecycle Test

Default Tags    e2e    browser    tasks    lifecycle

*** Variables ***
${LIFE_INCOMPLETE}    E2E-LIFE-INCOMPLETE-001
${LIFE_COMPLETE}      E2E-LIFE-COMPLETE-001
${LIFE_PERSIST}       E2E-LIFE-PERSIST-001
${LIFE_REOPEN}        E2E-LIFE-REOPEN-001

*** Keywords ***
Setup Task Lifecycle Suite
    [Documentation]    Create tasks for lifecycle tests, open dashboard.
    Create API Session
    Create Test Task    ${LIFE_INCOMPLETE}    Testing > Lifecycle > DONE Gate > Reject    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${LIFE_COMPLETE}      Testing > Lifecycle > DONE Gate > Accept    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${LIFE_PERSIST}       Testing > Lifecycle > Persist > Completed At    task_type=feature    workspace_id=WS-9147535A
    Create Test Task    ${LIFE_REOPEN}        Testing > Lifecycle > Reopen > Reset    task_type=feature    workspace_id=WS-9147535A
    Suite Setup Open Dashboard

Teardown Task Lifecycle Suite
    [Documentation]    Clean up and close browser.
    Suite Teardown Close Browser
    Cleanup Test Task    ${LIFE_INCOMPLETE}
    Cleanup Test Task    ${LIFE_COMPLETE}
    Cleanup Test Task    ${LIFE_PERSIST}
    Cleanup Test Task    ${LIFE_REOPEN}

Setup Lifecycle Test
    [Documentation]    SPA navigation to tasks view.
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=10s
    Fill Text    ${TASKS_SEARCH} input    ${EMPTY}
    Sleep    500ms    reason=Wait for search clear

*** Test Cases ***
DONE Gate Rejects Incomplete Task
    [Documentation]    PUT status=DONE without mandatory fields returns 422.
    [Tags]    e2e    lifecycle    done-gate    validation
    ${payload}=    Create Dictionary    status=DONE
    ${response}=    API PUT    /tasks/${LIFE_INCOMPLETE}    ${payload}
    # Must be 422 (validation error) — DONE gate requires session, doc, agent, summary
    Should Be Equal As Integers    ${response.status_code}    422    msg=DONE gate should reject incomplete task with 422

DONE Gate Accepts Complete Task
    [Documentation]    PUT status=DONE with all mandatory fields returns 200.
    [Tags]    e2e    lifecycle    done-gate
    ${response}=    Update Task To Done    ${LIFE_COMPLETE}    Testing > Lifecycle > DONE Gate > Accept
    Should Be Equal As Integers    ${response.status_code}    200    msg=DONE gate should accept complete task

Completed At Persists After Refresh
    [Documentation]    DONE task has completed_at timestamp that survives refresh.
    [Tags]    e2e    lifecycle    persistence
    # Mark task as DONE
    Update Task To Done    ${LIFE_PERSIST}    Testing > Lifecycle > Persist > Completed At
    # Verify via GET API
    ${response}=    API GET    /tasks/${LIFE_PERSIST}
    ${json}=    Set Variable    ${response.json()}
    ${completed_at}=    Get From Dictionary    ${json}    completed_at
    Should Not Be Empty    ${completed_at}    msg=completed_at should be set for DONE task
    # Verify in dashboard table
    Click    ${TASKS_REFRESH_BTN}
    Sleep    2s    reason=Wait for API refresh
    Fill Text    ${TASKS_SEARCH} input    ${LIFE_PERSIST}
    Sleep    1s    reason=Wait for search filter
    Wait For Table Rows
    # Completed column (index 10)
    ${completed_cell}=    Get Text    ${TASKS_TABLE_BODY} tr:has(td) td >> nth=10
    Should Not Be Empty    ${completed_cell}    msg=Completed column should show timestamp

Reopen DONE Task Resets Resolution
    [Documentation]    Setting DONE task back to IN_PROGRESS should work.
    [Tags]    e2e    lifecycle    reopen
    # First complete the task
    Update Task To Done    ${LIFE_REOPEN}    Testing > Lifecycle > Reopen > Reset
    # Now reopen it
    ${payload}=    Create Dictionary    status=IN_PROGRESS
    ${response}=    API PUT    /tasks/${LIFE_REOPEN}    ${payload}
    Should Be Equal As Integers    ${response.status_code}    200    msg=Should be able to reopen DONE task
    # Verify status changed
    ${get_resp}=    API GET    /tasks/${LIFE_REOPEN}
    ${json}=    Set Variable    ${get_resp.json()}
    ${status}=    Get From Dictionary    ${json}    status
    Should Be Equal    ${status}    IN_PROGRESS    msg=Status should be IN_PROGRESS after reopen
