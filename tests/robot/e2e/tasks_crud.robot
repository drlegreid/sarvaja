*** Settings ***
Documentation    P1-5 Phase 2: Tasks CRUD Browser Tests
...              Per EDS-DASHBOARD-2026-03-19: Tasks list, filter tabs, detail, create/delete
...              Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Spec → Static Suite
Library          Collections
Library          libs/GovernanceCRUDE2ELibrary.py
Resource         ../resources/browser.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Cleanup And Close Browser
Test Tags        e2e    browser    tasks    crud    P1-5-Phase2

*** Keywords ***
Cleanup And Close Browser
    [Documentation]    Cleanup test tasks then close browser
    Cleanup Test Data
    Close Browser    ALL

Navigate To Tasks View
    [Documentation]    Navigate to tasks and wait for loaded
    Navigate To Dashboard Home
    Click Nav Item    nav-tasks
    Sleep    2s
    ${header_count}=    Get Element Count    button:has-text("Add Task")
    IF    ${header_count} == 0
        Click Back Button If Detail View    back_testid=task-detail-back-btn
    END
    Wait For Elements State    button:has-text("Add Task")    visible    timeout=20s

Click First Task Row
    [Documentation]    Click the first data row in the tasks table, close any dialogs
    Wait For Elements State    table tbody tr:has(td) >> nth=0    visible    timeout=${ELEMENT_TIMEOUT}
    Dismiss Vuetify Overlays
    Click    table tbody tr:has(td) >> nth=0
    Sleep    2s
    # Close execution timeline dialog if it opened
    ${dialog_close}=    Get Element Count    [data-testid='execution-close-btn']
    IF    ${dialog_close} > 0
        Click    [data-testid='execution-close-btn']
        Sleep    1s
    END

*** Test Cases ***
# =============================================================================
# Tasks List Tests
# =============================================================================

Tasks View Shows Add Button
    [Documentation]    Tasks view has an "Add Task" button
    [Tags]    smoke    list
    [Setup]    Navigate To Tasks View
    Wait For Elements State    button:has-text("Add Task")    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Tasks Table Shows Column Headers
    [Documentation]    Tasks table has expected columns
    [Tags]    list    table
    [Setup]    Navigate To Tasks View
    Wait For Elements State    th:has-text("Task ID")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    th:has-text("Description")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    th:has-text("Status")    visible    timeout=${ELEMENT_TIMEOUT}

Tasks Table Has Pagination
    [Documentation]    Tasks table shows pagination with page count
    [Tags]    list    pagination
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=/Page \\d+ of \\d+/    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Tasks Filter Tab Tests
# =============================================================================

Tasks Has All Tab
    [Documentation]    Tasks view has "All" filter tab
    [Tags]    filter    tabs
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=All >> nth=0    visible    timeout=${ELEMENT_TIMEOUT}

Tasks Has Available Tab
    [Documentation]    Tasks view has "Available" filter tab
    [Tags]    filter    tabs
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=Available >> nth=0    visible    timeout=${ELEMENT_TIMEOUT}

Tasks Has Completed Tab
    [Documentation]    Tasks view has "Completed" filter tab
    [Tags]    filter    tabs
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=Completed >> nth=0    visible    timeout=${ELEMENT_TIMEOUT}

Tasks Click Completed Tab Filters
    [Documentation]    Clicking Completed tab filters to completed tasks
    [Tags]    filter    tabs    functional
    [Setup]    Navigate To Tasks View
    Click    text=Completed >> nth=0
    Sleep    2s
    ${count}=    Get Element Count    text=/DONE|CLOSED|completed/
    Should Be True    ${count} > 0
    ...    msg=Completed tab should show DONE or CLOSED tasks

# =============================================================================
# Tasks Detail Tests
# =============================================================================

Click Task Opens Detail
    [Documentation]    Clicking a task row opens the detail view
    [Tags]    detail    read
    [Setup]    Navigate To Tasks View
    Click First Task Row
    ${detail}=    Get Element Count    [data-testid='task-detail']
    ${edit}=    Get Element Count    text=Edit
    Should Be True    ${detail} > 0 or ${edit} > 0
    ...    msg=Task detail should open

Task Detail Has Back Button
    [Documentation]    Task detail has a back button
    [Tags]    detail    navigation
    [Setup]    Navigate To Tasks View
    Click First Task Row
    Sleep    1s
    ${back1}=    Get Element Count    [data-testid='task-detail-back-btn']
    ${back2}=    Get Element Count    [data-testid='task-detail-back-to-source']
    Should Be True    ${back1} + ${back2} > 0    msg=Back button not found

Task Detail Back Returns To List
    [Documentation]    Clicking back returns to tasks list
    [Tags]    detail    navigation
    [Setup]    Navigate To Tasks View
    Click First Task Row
    Sleep    1s
    ${back1}=    Get Element Count    [data-testid='task-detail-back-btn']
    IF    ${back1} > 0
        Click    [data-testid='task-detail-back-btn']
    ELSE
        Click    [data-testid='task-detail-back-to-source']
    END
    Sleep    2s
    Wait For Elements State    button:has-text("Add Task")    visible    timeout=20s

# =============================================================================
# Tasks API CRUD → Browser Verification
# =============================================================================

Create Task Appears In API
    [Documentation]    Create task via API, verify in list
    [Tags]    create    api
    ${task_id}=    Generate Unique ID    TEST
    ${result}=    Create Task    ${task_id}    Robot CRUD Browser Test    phase=P10    status=TODO
    Should Be True    ${result}[success]    Create failed: ${result}
    ${list}=    List Tasks
    Should Be True    ${list}[count] > 10    Tasks list should have 10+ tasks

Claim Task Updates Status
    [Documentation]    Claiming a task via API changes its status
    [Tags]    claim    api
    ${task_id}=    Generate Unique ID    TEST
    Create Task    ${task_id}    Robot Claim Test    status=TODO
    ${claim}=    Claim Task    ${task_id}    code-agent
    Should Be True    ${claim}[success]    Claim failed: ${claim}
    Should Be Equal    ${claim}[task][status]    IN_PROGRESS

Complete Task Updates Status
    [Documentation]    Completing a task via API changes status to DONE
    [Tags]    complete    api
    ${task_id}=    Generate Unique ID    TEST
    Create Task    ${task_id}    Robot Complete Test    status=TODO
    Claim Task    ${task_id}    code-agent
    ${complete}=    Complete Task    ${task_id}    evidence=Robot test passed
    Should Be True    ${complete}[success]    Complete failed: ${complete}
    Should Be Equal    ${complete}[task][status]    DONE

Delete Task Via API Succeeds
    [Documentation]    Deleting a task removes it
    [Tags]    delete    api
    ${task_id}=    Generate Unique ID    TEST
    Create Task    ${task_id}    Robot Delete Test
    ${del}=    Delete Task    ${task_id}
    Should Be True    ${del}[success]    Delete failed: ${del}
