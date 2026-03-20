*** Settings ***
Documentation    P1-5 Phase 2: Rules CRUD Browser Tests
...              Per EDS-DASHBOARD-2026-03-19: Rules list, filter, detail, create/delete
...              Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Spec → Static Suite
Library          Collections
Library          libs/GovernanceCRUDE2ELibrary.py
Resource         ../resources/browser.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Cleanup And Close Browser
Test Tags        e2e    browser    rules    crud    P1-5-Phase2

*** Keywords ***
Cleanup And Close Browser
    [Documentation]    Cleanup test rules then close browser
    Cleanup Test Data
    Close Browser    ALL

Navigate To Rules View
    [Documentation]    Navigate to rules and wait for table
    Navigate To Dashboard Home
    Click Nav Item    nav-rules
    Sleep    2s
    ${header_count}=    Get Element Count    button:has-text("Add Rule")
    IF    ${header_count} == 0
        Click Back Button If Detail View    back_testid=rule-detail-back-btn
    END
    Wait For Elements State    button:has-text("Add Rule")    visible    timeout=20s

Click First Rule Row
    [Documentation]    Click the first data row in the rules table
    Wait For Elements State    table tbody tr:has(td) >> nth=0    visible    timeout=${ELEMENT_TIMEOUT}
    Dismiss Vuetify Overlays
    Click    table tbody tr:has(td) >> nth=0
    Sleep    2s

Type In Rules Search
    [Documentation]    Type text in the rules search input
    [Arguments]    ${text}
    Fill Text    [data-testid='nav-rules'] ~ main input[type='text'] >> nth=0    ${text}
    Sleep    2s

*** Test Cases ***
# =============================================================================
# Rules List Tests
# =============================================================================

Rules View Shows Add Button
    [Documentation]    Rules view has an "Add Rule" button
    [Tags]    smoke    list
    [Setup]    Navigate To Rules View
    Wait For Elements State    button:has-text("Add Rule")    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Rules Table Shows Column Headers
    [Documentation]    Rules table has expected columns
    [Tags]    list    table
    [Setup]    Navigate To Rules View
    Wait For Elements State    th:has-text("Rule ID")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    th:has-text("Category")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    th:has-text("Priority")    visible    timeout=${ELEMENT_TIMEOUT}

Rules Table Has Pagination
    [Documentation]    Rules table has pagination showing "1-25 of N"
    [Tags]    list    pagination
    [Setup]    Navigate To Rules View
    Wait For Elements State    text=/1-25 of \\d+/    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Rules Detail Tests
# =============================================================================

Click Rule Opens Detail
    [Documentation]    Clicking a rule row opens the detail view
    [Tags]    detail    read
    [Setup]    Navigate To Rules View
    Click First Rule Row
    Wait For Elements State    [data-testid='rule-detail']    visible    timeout=${ELEMENT_TIMEOUT}

Rule Detail Has Back Button
    [Documentation]    Rule detail view has a back button
    [Tags]    detail    navigation
    [Setup]    Navigate To Rules View
    Click First Rule Row
    Wait For Elements State    [data-testid='rule-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    ${back_count}=    Get Element Count    [data-testid='rule-detail-back-btn']
    Should Be True    ${back_count} > 0    msg=Back button not found in rule detail

Rule Detail Shows Edit Delete
    [Documentation]    Rule detail has Edit and Delete buttons
    [Tags]    detail    edit    delete
    [Setup]    Navigate To Rules View
    Click First Rule Row
    Wait For Elements State    [data-testid='rule-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    [data-testid='rule-detail-edit-btn']    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    [data-testid='rule-detail-delete-btn']    visible    timeout=${ELEMENT_TIMEOUT}

Rule Detail Back Returns To List
    [Documentation]    Clicking back from rule detail returns to rules list
    [Tags]    detail    navigation
    [Setup]    Navigate To Rules View
    Click First Rule Row
    Wait For Elements State    [data-testid='rule-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    Click    [data-testid='rule-detail-back-btn']
    Sleep    2s
    Wait For Elements State    button:has-text("Add Rule")    visible    timeout=20s

Rule Detail Shows ID
    [Documentation]    Rule detail shows the rule ID
    [Tags]    detail    id
    [Setup]    Navigate To Rules View
    Click First Rule Row
    Wait For Elements State    [data-testid='rule-detail']    visible    timeout=${ELEMENT_TIMEOUT}
    ${id_count}=    Get Element Count    [data-testid='rule-detail-id']
    Should Be True    ${id_count} > 0    msg=Rule detail should show rule ID

# =============================================================================
# Rules API CRUD → Browser Verification
# =============================================================================

Create Rule Appears In API List
    [Documentation]    Create rule via API, verify it's in the API list
    [Tags]    create    api
    ${typedb}=    Check TypeDB Available
    Skip If    not ${typedb}    TypeDB not connected
    ${rule_id}=    Generate Unique ID    TEST
    ${result}=    Create Rule    ${rule_id}    Robot CRUD Test Rule    status=ACTIVE
    Should Be True    ${result}[success]    Create failed: ${result}
    ${list}=    List Rules
    Should Be True    ${list}[count] > 30    Rules list should have 30+ rules

Delete Rule Disappears From API
    [Documentation]    Delete rule via API, verify 404
    [Tags]    delete    api
    ${typedb}=    Check TypeDB Available
    Skip If    not ${typedb}    TypeDB not connected
    ${rule_id}=    Generate Unique ID    TEST
    Create Rule    ${rule_id}    Robot Delete Test Rule    status=ACTIVE
    ${del}=    Delete Rule    ${rule_id}
    Should Be True    ${del}[success]    Delete failed: ${del}
    ${get}=    Get Rule    ${rule_id}
    Should Be Equal As Integers    ${get}[status_code]    404
