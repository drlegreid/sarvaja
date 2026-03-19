*** Settings ***
Documentation    Dashboard Navigation E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              Migrated from: tests/e2e/test_dashboard_e2e.py::TestDashboardNavigation

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Test Setup Navigate Home

Default Tags    e2e    browser    navigation

*** Test Cases ***
Dashboard Loads With Title
    [Documentation]    Dashboard loads with header and navigation sidebar.
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=10s

Header Shows Rules Count Chip
    [Documentation]    Header displays rule count chip.
    Wait For Elements State    ${TOOLBAR_RULES_CHIP}    visible    timeout=10s

Header Shows Decisions Count Chip
    [Documentation]    Header displays decision count chip.
    Wait For Elements State    ${TOOLBAR_DECISIONS_CHIP}    visible    timeout=10s

Core Navigation Tabs Are Present
    [Documentation]    All 17 navigation tabs are visible in the sidebar.
    Navigation Tab Should Be Visible    chat
    Navigation Tab Should Be Visible    rules
    Navigation Tab Should Be Visible    agents
    Navigation Tab Should Be Visible    tasks
    Navigation Tab Should Be Visible    sessions
    Navigation Tab Should Be Visible    executive
    Navigation Tab Should Be Visible    decisions
    Navigation Tab Should Be Visible    impact
    Navigation Tab Should Be Visible    trust
    Navigation Tab Should Be Visible    workflow
    Navigation Tab Should Be Visible    audit
    Navigation Tab Should Be Visible    monitor
    Navigation Tab Should Be Visible    infra
    Navigation Tab Should Be Visible    metrics
    Navigation Tab Should Be Visible    tests
    Navigation Tab Should Be Visible    projects
    Navigation Tab Should Be Visible    workspaces

Navigate To Rules View
    [Documentation]    Clicking Rules tab loads the Governance Rules page.
    Navigate And Verify Tab    rules    Governance Rules

Navigate To Agents View
    [Documentation]    Clicking Agents tab loads the Registered Agents page.
    Navigate And Verify Tab    agents    Registered Agents

Navigate To Tasks View
    [Documentation]    Clicking Tasks tab loads the Tasks page.
    Navigate To Tab    tasks
    Wait For Elements State    [data-testid='tasks-list']    visible    timeout=10s

Navigate To Sessions View
    [Documentation]    Clicking Sessions tab loads the Session Evidence page.
    Navigate And Verify Tab    sessions    Session Evidence

Navigate To Trust View
    [Documentation]    Clicking Trust tab loads the Agent Trust Dashboard.
    Navigate And Verify Tab    trust    Agent Trust Dashboard

Navigate To Workspaces View
    [Documentation]    Clicking Workspaces tab loads the Workspaces page.
    Navigate To Tab    workspaces
    Wait For Elements State    [data-testid='workspaces-list']    visible    timeout=10s

Navigate To Projects View
    [Documentation]    Clicking Projects tab loads the Projects page.
    Navigate To Tab    projects
    Wait For Elements State    [data-testid='projects-list']    visible    timeout=10s

Navigate To Infrastructure View
    [Documentation]    Clicking Infrastructure tab loads the Infrastructure Health page.
    Navigate And Verify Tab    infra    Infrastructure Health

Navigate To Chat View
    [Documentation]    Clicking Chat tab loads the Agent Chat page.
    Navigate To Tab    chat
    Wait For Elements State    [data-testid='chat-view']    visible    timeout=10s
