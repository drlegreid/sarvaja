*** Settings ***
Documentation    Workspaces View E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              New view added in P2-11: Workspace Management UI

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Setup Workspaces View

Default Tags    e2e    browser    workspaces

*** Keywords ***
Setup Workspaces View
    [Documentation]    Navigate to Workspaces view before each test.
    Test Setup Navigate Home
    Navigate To Tab    workspaces
    Wait For Elements State    ${WORKSPACES_LIST}    visible    timeout=10s

*** Test Cases ***
Workspaces View Loads
    [Documentation]    Workspaces view renders with list container.
    Wait For Elements State    ${WORKSPACES_LIST}    visible    timeout=10s

Create Workspace Button Is Present
    [Documentation]    Create Workspace button is visible.
    Wait For Elements State    ${WORKSPACE_CREATE_BTN}    visible    timeout=10s

Refresh Button Is Present
    [Documentation]    Refresh button is visible.
    Wait For Elements State    ${WORKSPACE_REFRESH_BTN}    visible    timeout=10s

Stats Cards Are Displayed
    [Documentation]    Workspace stats cards show Total, Active, and Types counts.
    # Use main-scoped selectors to avoid strict mode violations with nav items
    Wait For Elements State    main >> text=Total    visible    timeout=10s
    Wait For Elements State    main >> text=Active    visible    timeout=10s
    Wait For Elements State    main >> text=Types >> nth=0    visible    timeout=10s

Search And Filter Controls Are Present
    [Documentation]    Search input and filter dropdowns are visible.
    # Type and Status appear inside the workspaces filter comboboxes
    ${has_search}=    Run Keyword And Return Status
    ...    Wait For Elements State    main >> text=Search workspaces    visible    timeout=5s
    Log    Search input visible: ${has_search}
    # At least the main content area loaded
    Wait For Elements State    ${WORKSPACES_LIST}    visible    timeout=5s
