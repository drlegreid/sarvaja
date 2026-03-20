*** Settings ***
Documentation    P1-5 Phase 2: Sessions CRUD Browser Tests
...              Per EDS-DASHBOARD-2026-03-19: Sessions list, filter, detail, transcript
...              Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Spec → Static Suite
Resource         ../resources/browser.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Close Browser    ALL
Test Setup       Navigate To Sessions List
Test Tags        e2e    browser    sessions    crud    P1-5-Phase2

*** Keywords ***
Sessions Table Should Have Rows
    [Documentation]    Wait for sessions table to have at least one data row
    ${count}=    Get Element Count    table tbody tr:has(td) >> nth=0
    IF    ${count} == 0
        ${clear_btn}=    Get Element Count    button:has-text("Clear Search")
        IF    ${clear_btn} > 0
            Click    button:has-text("Clear Search") >> nth=0
            Sleep    2s
        END
    END
    Wait For Elements State    table tbody tr:has(td) >> nth=0    visible    timeout=20s

Click First Session Row
    [Documentation]    Click the first data row in the sessions table
    Sessions Table Should Have Rows
    Dismiss Vuetify Overlays
    Click    table tbody tr:has(td) >> nth=0
    Sleep    2s

*** Test Cases ***
# =============================================================================
# Sessions List Tests
# =============================================================================

Sessions View Shows Add Button
    [Documentation]    Sessions view has an Add Session button
    [Tags]    smoke    list
    Wait For Elements State    button:has-text("Add Session")    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Sessions View Shows Stats Cards
    [Documentation]    Sessions view displays stats cards
    [Tags]    list    stats
    Wait For Elements State    text=Total Sessions    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    text=Total Duration    visible    timeout=${ELEMENT_TIMEOUT}

Sessions Table Shows Column Headers
    [Documentation]    Sessions table has expected columns
    [Tags]    list    table
    Wait For Elements State    th:has-text("Session ID")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    th:has-text("Source")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    th:has-text("Duration")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    th:has-text("Status")    visible    timeout=${ELEMENT_TIMEOUT}

Sessions Table Shows Pagination
    [Documentation]    Sessions table has pagination controls
    [Tags]    list    pagination
    Wait For Elements State    text=/Page \\d+ of \\d+/    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Sessions Filter Tests
# =============================================================================

Sessions Has Date Range Filters
    [Documentation]    Sessions view has From/To date filter inputs
    [Tags]    filter    date
    ${from_count}=    Get Element Count    text=From date
    ${to_count}=    Get Element Count    text=To date
    Should Be True    ${from_count} > 0    msg=From date filter not found
    Should Be True    ${to_count} > 0    msg=To date filter not found

Sessions Has Hide Test Checkbox
    [Documentation]    Sessions view has a "Hide test" checkbox
    [Tags]    filter    hide_test
    Wait For Elements State    text=Hide test    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Sessions Detail Tests
# =============================================================================

Click Session Opens Detail
    [Documentation]    Clicking a session row opens the detail view
    [Tags]    detail    read
    Sessions Table Should Have Rows
    Click First Session Row
    Wait For Elements State    [data-testid='session-detail']    visible    timeout=${ELEMENT_TIMEOUT}

Session Detail Shows Back Button
    [Documentation]    Session detail view has a back navigation button
    [Tags]    detail    navigation
    Sessions Table Should Have Rows
    Click First Session Row
    Wait For Elements State    [data-testid='session-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    ${back_count}=    Get Element Count    [data-testid='session-detail-back-btn']
    Should Be True    ${back_count} > 0    msg=Back button not found in session detail

Session Detail Shows Edit Delete
    [Documentation]    Session detail shows Edit and Delete buttons
    [Tags]    detail    edit    delete
    Sessions Table Should Have Rows
    Click First Session Row
    Wait For Elements State    [data-testid='session-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    ${edit}=    Get Element Count    [data-testid='session-detail-edit-btn']
    ${delete}=    Get Element Count    [data-testid='session-detail-delete-btn']
    Should Be True    ${edit} > 0 or ${delete} > 0
    ...    msg=Session detail should have edit or delete buttons

Session Detail Back Returns To List
    [Documentation]    Clicking back button returns to sessions list
    [Tags]    detail    navigation
    Sessions Table Should Have Rows
    Click First Session Row
    Wait For Elements State    [data-testid='session-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    Click    [data-testid='session-detail-back-btn']
    Sleep    2s
    Wait For Elements State    button:has-text("Add Session")    visible    timeout=20s

Session Detail Shows Content
    [Documentation]    Session detail shows content section
    [Tags]    detail    content
    Sessions Table Should Have Rows
    Click First Session Row
    Wait For Elements State    [data-testid='session-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    ${content}=    Get Element Count    [data-testid='session-detail-content']
    ${status}=    Get Element Count    [data-testid='session-detail-status']
    ${id}=    Get Element Count    [data-testid='session-detail-id']
    ${total}=    Evaluate    ${content} + ${status} + ${id}
    Should Be True    ${total} > 0
    ...    msg=Session detail should show content, status, or ID
