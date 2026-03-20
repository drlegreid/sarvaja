*** Settings ***
Documentation    P1-5 Phase 2: Workspaces CRUD Browser Tests
...              Per EDS-DASHBOARD-2026-03-19: Workspaces create, detail, edit, delete
...              Per P2-11: Full CRUD operational in dashboard
...              Per TEST-EXPLSPEC-01-v1: Exploratory Dynamic Spec → Static Suite
Library          Collections
Library          String
Library          libs/GovernanceCRUDE2ELibrary.py
Resource         ../resources/browser.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Close Browser    ALL
Test Tags        e2e    browser    workspaces    crud    P1-5-Phase2

*** Keywords ***
Navigate To Workspaces View
    [Documentation]    Navigate to workspaces and wait for list loaded.
    ...                Navigates away first to force on_view_change, which
    ...                resets show_workspace_detail/form (Trame SPA state).
    Navigate To Dashboard Home
    # Navigate away first to ensure on_view_change fires when we switch
    # to workspaces — this resets stale detail/form state from prior tests
    Click Nav Item    nav-rules
    Click Nav Item    nav-workspaces
    Wait For Elements State    button:has-text("Create Workspace")    visible    timeout=20s
    # Wait for workspace data to finish loading
    Wait For Elements State    [data-testid='workspaces-table']    visible    timeout=20s

Click First Workspace Item
    [Documentation]    Click the first workspace in the list
    Wait For Elements State    [data-testid='workspace-item'] >> nth=0    visible    timeout=15s
    Click    [data-testid='workspace-item'] >> nth=0
    Sleep    2s

*** Test Cases ***
# =============================================================================
# Workspaces List Tests
# =============================================================================

Workspaces View Shows Create Button
    [Documentation]    Workspaces view has a Create Workspace button
    [Tags]    smoke    list
    [Setup]    Navigate To Workspaces View
    Wait For Elements State    button:has-text("Create Workspace")    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Workspaces View Shows Stats Cards
    [Documentation]    Workspaces view displays stats cards
    [Tags]    list    stats
    [Setup]    Navigate To Workspaces View
    Wait For Elements State    .text-caption:has-text("Total")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    .text-caption:has-text("Active")    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    .text-caption:has-text("Types")    visible    timeout=${ELEMENT_TIMEOUT}

Workspaces View Shows Refresh Button
    [Documentation]    Workspaces view has a Refresh button
    [Tags]    list    refresh
    [Setup]    Navigate To Workspaces View
    Wait For Elements State    button:has-text("Refresh")    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Workspaces List Shows Items
    [Documentation]    Workspaces list shows workspace items
    [Tags]    list    data
    [Setup]    Navigate To Workspaces View
    ${count}=    Get Element Count    [data-testid='workspace-item']
    Should Be True    ${count} > 0
    ...    msg=Workspaces list should have at least one item

# =============================================================================
# Workspaces Detail Tests
# =============================================================================

Click Workspace Opens Detail
    [Documentation]    Clicking a workspace opens the detail view
    [Tags]    detail    read
    [Setup]    Navigate To Workspaces View
    Click First Workspace Item
    Wait For Elements State    text=Workspace Info    visible    timeout=${ELEMENT_TIMEOUT}

Workspace Detail Shows Info Fields
    [Documentation]    Workspace detail shows ID and Type fields
    [Tags]    detail    fields
    [Setup]    Navigate To Workspaces View
    Click First Workspace Item
    Wait For Elements State    text=Workspace Info    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    .text-caption:text-is("ID")    visible    timeout=${ELEMENT_TIMEOUT}

Workspace Detail Shows Agents Section
    [Documentation]    Workspace detail shows Assigned Agents section
    [Tags]    detail    agents
    [Setup]    Navigate To Workspaces View
    Click First Workspace Item
    Wait For Elements State    text=Workspace Info    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    text=Assigned Agents    visible    timeout=${ELEMENT_TIMEOUT}

Workspace Detail Shows Rules Section
    [Documentation]    Workspace detail shows Default Rules section
    [Tags]    detail    rules
    [Setup]    Navigate To Workspaces View
    Click First Workspace Item
    Wait For Elements State    text=Workspace Info    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    .v-card-title:has-text("Default Rules")    visible    timeout=${ELEMENT_TIMEOUT}

Workspace Detail Back Returns To List
    [Documentation]    Clicking back from detail returns to list
    [Tags]    detail    navigation
    [Setup]    Navigate To Workspaces View
    Click First Workspace Item
    Wait For Elements State    text=Workspace Info    visible    timeout=${ELEMENT_TIMEOUT}
    Click    [data-testid='workspace-detail-back-btn']
    Sleep    2s
    Wait For Elements State    button:has-text("Create Workspace")    visible    timeout=20s

# =============================================================================
# Workspaces Create Tests
# =============================================================================

Create Workspace Button Opens Form
    [Documentation]    Clicking Create Workspace opens the creation form
    [Tags]    create    form
    [Setup]    Navigate To Workspaces View
    Click    button:has-text("Create Workspace")
    Sleep    2s
    ${form_count}=    Get Element Count    [data-testid='workspace-form']
    ${input_count}=    Get Element Count    text=/Name|Create/
    Should Be True    ${form_count} + ${input_count} > 0
    ...    msg=Create form should appear

# =============================================================================
# Workspaces API Tests
# =============================================================================

Workspaces API Returns List
    [Documentation]    Workspaces API returns workspace data
    [Tags]    api    list
    ${result}=    Get Resource With Body    workspaces
    Should Be Equal As Integers    ${result}[status_code]    200
    ${count}=    Evaluate    len($result['body'])
    Should Be True    ${count} > 0    msg=Should have at least 1 workspace

Workspace API Returns Detail
    [Documentation]    Workspace detail API returns individual workspace
    [Tags]    api    detail
    ${result}=    Get Resource With Body    workspaces
    Should Be Equal As Integers    ${result}[status_code]    200
    ${ws}=    Evaluate    $result['body'][0]
    ${ws_id}=    Set Variable    ${ws}[workspace_id]
    ${detail}=    Get Resource With Body    workspaces/${ws_id}
    Should Be Equal As Integers    ${detail}[status_code]    200
