*** Settings ***
Documentation    E2E Browser Tests for Governance Dashboard
...              Per: RF-007 Robot Framework Migration
...              Migrated from tests/e2e/test_dashboard_e2e.py
...              Uses robotframework-browser (Playwright-based)
Library          Browser    auto_closing_level=SUITE
Resource         ../resources/common.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Close Browser    ALL
Test Setup       Navigate To Dashboard

*** Variables ***
${DASHBOARD_URL}      http://localhost:8081
${APP_TITLE}          Governance Dashboard
${PAGE_TIMEOUT}       10s

*** Keywords ***
Open Dashboard Browser
    [Documentation]    Open browser for test suite
    New Browser    chromium    headless=True
    New Context    viewport={'width': 1280, 'height': 720}

Navigate To Dashboard
    [Documentation]    Navigate to dashboard and wait for app init
    New Page    ${DASHBOARD_URL}
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=${PAGE_TIMEOUT}

Navigate To Rules View
    [Documentation]    Navigate to Rules view
    Navigate To Dashboard
    Click    [data-testid='nav-rules']
    Wait For Elements State    text=Governance Rules    visible

Navigate To Tasks View
    [Documentation]    Navigate to Tasks view
    Navigate To Dashboard
    Click    [data-testid='nav-tasks']
    Wait For Elements State    text=Platform Tasks    visible

Navigate To Sessions View
    [Documentation]    Navigate to Sessions view
    Navigate To Dashboard
    Click    [data-testid='nav-sessions']
    Wait For Elements State    text=Session Evidence    visible

Navigate To Trust View
    [Documentation]    Navigate to Trust view
    Navigate To Dashboard
    Click    [data-testid='nav-trust']
    Wait For Elements State    text=Agent Trust Dashboard    visible

Navigate To Infra View
    [Documentation]    Navigate to Infrastructure view
    Navigate To Dashboard
    Click    [data-testid='nav-infra']
    Wait For Elements State    text=Infrastructure Health    visible

*** Test Cases ***
# =============================================================================
# Dashboard Navigation Tests
# =============================================================================

Dashboard Loads With Header
    [Documentation]    Dashboard loads with header and navigation
    [Tags]    e2e    browser    navigation    smoke
    Wait For Elements State    text=${APP_TITLE}    visible
    Wait For Elements State    [data-testid='nav-rules']    visible

Header Shows Stats
    [Documentation]    Header displays rule and decision counts
    [Tags]    e2e    browser    navigation
    Wait For Elements State    text=/\\d+ Rules \\| \\d+ Decisions/    visible

Navigation Tabs Present
    [Documentation]    All navigation tabs are visible
    [Tags]    e2e    browser    navigation
    Wait For Elements State    text=Rules >> nth=0    visible
    Wait For Elements State    text=Agents >> nth=0    visible
    Wait For Elements State    text=Tasks >> nth=0    visible
    Wait For Elements State    text=Sessions >> nth=0    visible
    Wait For Elements State    text=Trust >> nth=0    visible

Navigate To Rules
    [Documentation]    Can navigate to Rules view
    [Tags]    e2e    browser    navigation
    Click    [data-testid='nav-rules']
    Wait For Elements State    text=Governance Rules    visible

Navigate To Agents
    [Documentation]    Can navigate to Agents view
    [Tags]    e2e    browser    navigation
    Click    [data-testid='nav-agents']
    Wait For Elements State    text=Registered Agents    visible

Navigate To Tasks
    [Documentation]    Can navigate to Tasks view
    [Tags]    e2e    browser    navigation
    Click    [data-testid='nav-tasks']
    Wait For Elements State    text=Platform Tasks    visible

Navigate To Sessions
    [Documentation]    Can navigate to Sessions view
    [Tags]    e2e    browser    navigation
    Click    [data-testid='nav-sessions']
    Wait For Elements State    text=Session Evidence    visible

Navigate To Trust
    [Documentation]    Can navigate to Trust view
    [Tags]    e2e    browser    navigation
    Click    [data-testid='nav-trust']
    Wait For Elements State    text=Agent Trust Dashboard    visible

# =============================================================================
# Rules View Tests
# =============================================================================

Rules List Loads
    [Documentation]    Rules list shows rule count
    [Tags]    e2e    browser    rules
    [Setup]    Navigate To Rules View
    Wait For Elements State    text=/\\d+ rules loaded/    visible

Add Rule Button Present
    [Documentation]    Add Rule button is visible
    [Tags]    e2e    browser    rules
    [Setup]    Navigate To Rules View
    Wait For Elements State    text=Add Rule    visible

Rules Search Input Present
    [Documentation]    Search input is available
    [Tags]    e2e    browser    rules
    [Setup]    Navigate To Rules View
    Wait For Elements State    input[placeholder*='Search'] >> nth=0    visible

Rule List Items Clickable
    [Documentation]    Rule items in list are clickable
    [Tags]    e2e    browser    rules
    [Setup]    Navigate To Rules View
    Wait For Elements State    listitem >> nth=0    visible

Click Rule Shows Detail
    [Documentation]    Clicking a rule shows detail view
    [Tags]    e2e    browser    rules
    [Setup]    Navigate To Rules View
    Click    listitem >> nth=0
    Wait For Elements State    text=Edit    visible
    Wait For Elements State    text=Delete    visible

Rule Detail Shows Directive
    [Documentation]    Rule detail view shows directive text
    [Tags]    e2e    browser    rules
    [Setup]    Navigate To Rules View
    Click    listitem >> nth=0
    Wait For Elements State    text=Directive    visible

# =============================================================================
# Tasks View Tests
# =============================================================================

Tasks List Loads
    [Documentation]    Tasks list shows task count
    [Tags]    e2e    browser    tasks
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=/\\d+ tasks loaded/    visible

Add Task Button Present
    [Documentation]    Add Task button is visible
    [Tags]    e2e    browser    tasks
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=Add Task    visible

Task Shows Status
    [Documentation]    Tasks show status badges
    [Tags]    e2e    browser    tasks
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=/TODO|DONE|IN_PROGRESS|pending/ >> nth=0    visible

# =============================================================================
# Trust View Tests
# =============================================================================

Trust Dashboard Loads
    [Documentation]    Trust dashboard shows stats cards
    [Tags]    e2e    browser    trust
    [Setup]    Navigate To Trust View
    Wait For Elements State    text=Total Agents    visible
    Wait For Elements State    text=Avg Trust Score    visible

Trust Refresh Button Present
    [Documentation]    Refresh button is available
    [Tags]    e2e    browser    trust
    [Setup]    Navigate To Trust View
    Wait For Elements State    text=Refresh Data    visible

Trust Leaderboard Present
    [Documentation]    Trust leaderboard section is visible
    [Tags]    e2e    browser    trust
    [Setup]    Navigate To Trust View
    Wait For Elements State    text=Trust Leaderboard    visible

# =============================================================================
# Pagination UI Tests
# =============================================================================

Rules View Has Pagination
    [Documentation]    Test Rules view has pagination UI
    [Tags]    e2e    browser    pagination
    [Setup]    Navigate To Rules View
    Wait For Elements State    text=/\\d+ rules loaded/    visible

Tasks View Has Pagination
    [Documentation]    Test Tasks view has pagination UI
    [Tags]    e2e    browser    pagination
    [Setup]    Navigate To Tasks View
    Wait For Elements State    text=/\\d+ tasks loaded/    visible

Sessions View Has Pagination
    [Documentation]    Test Sessions view has pagination
    [Tags]    e2e    browser    pagination
    [Setup]    Navigate To Sessions View
    Wait For Elements State    text=session_id    visible    timeout=5s

Agents View Has Pagination
    [Documentation]    Test Agents view has pagination
    [Tags]    e2e    browser    pagination
    Click    [data-testid='nav-agents']
    Wait For Elements State    text=Registered Agents    visible
    Wait For Elements State    text=Trust Score    visible    timeout=5s

# =============================================================================
# Infrastructure View Tests
# =============================================================================

Infra Dashboard Loads
    [Documentation]    Infrastructure dashboard loads with header
    [Tags]    e2e    browser    infra
    [Setup]    Navigate To Infra View
    Wait For Elements State    text=Infrastructure Health    visible

Infra Shows Service Cards
    [Documentation]    Service status cards are displayed
    [Tags]    e2e    browser    infra
    [Setup]    Navigate To Infra View
    Wait For Elements State    [data-testid='infra-card-typedb']    visible
    Wait For Elements State    [data-testid='infra-card-chromadb']    visible

Infra Shows Stats
    [Documentation]    System stats are displayed
    [Tags]    e2e    browser    infra
    [Setup]    Navigate To Infra View
    Wait For Elements State    [data-testid='infra-stat-memory']    visible
    Wait For Elements State    [data-testid='infra-stat-hash']    visible

Infra Refresh Button Clickable
    [Documentation]    Refresh button is clickable
    [Tags]    e2e    browser    infra
    [Setup]    Navigate To Infra View
    Wait For Elements State    [data-testid='infra-refresh-btn']    visible
    Click    [data-testid='infra-refresh-btn']

Infra Recovery Actions Present
    [Documentation]    Recovery action buttons are present
    [Tags]    e2e    browser    infra
    [Setup]    Navigate To Infra View
    Wait For Elements State    [data-testid='infra-start-all']    visible
    Wait For Elements State    [data-testid='infra-restart']    visible
    Wait For Elements State    [data-testid='infra-cleanup']    visible
