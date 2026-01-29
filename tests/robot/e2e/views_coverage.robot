*** Settings ***
Documentation    RF-010: Extended View Coverage Tests
...              Per GAP-UI-AUDIT-002: Cover untested dashboard views
...              Views: Decisions, Agents detail, Search, Executive
...              Per ARCH-EBMSF-01-v1: Evidence-based assertions with msg=
Library          Browser    auto_closing_level=SUITE
Resource         ../resources/common.resource
Suite Setup      Open Dashboard Browser
Suite Teardown   Close Browser    ALL
Test Setup       Navigate To Dashboard Home
Test Tags        e2e    browser    views    ui    TEST-BDD-01-v1

*** Variables ***
${DASHBOARD_URL}      http://localhost:8081
${APP_TITLE}          Sarvaja Governance Dashboard
${PAGE_TIMEOUT}       10s
${ELEMENT_TIMEOUT}    10s

*** Keywords ***
Open Dashboard Browser
    [Documentation]    Open browser for test suite
    New Browser    chromium    headless=True
    New Context    viewport={'width': 1280, 'height': 720}
    New Page    ${DASHBOARD_URL}
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=${PAGE_TIMEOUT}

Navigate To Dashboard Home
    [Documentation]    Navigate to dashboard and wait for app init
    Go To    ${DASHBOARD_URL}
    Reload
    Wait For Elements State    text=${APP_TITLE}    visible    timeout=20s

Navigate To Decisions List
    [Documentation]    Navigate to Decisions list (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-decisions']
    Sleep    1s
    # SPA may open to decision detail if previously selected
    ${list_count}=    Get Element Count    [data-testid='decision-log']
    IF    ${list_count} == 0
        # In detail view - click back button (data-testid preferred)
        ${back_testid}=    Get Element Count    [data-testid='decision-detail-back-btn']
        IF    ${back_testid} > 0
            Click    [data-testid='decision-detail-back-btn']
        ELSE
            ${back_count}=    Get Element Count    button:has-text("󰁍")
            IF    ${back_count} > 0
                Click    button:has-text("󰁍") >> nth=0
            END
        END
    END
    Wait For Elements State    [data-testid='decision-log']    visible    timeout=20s

Navigate To Agents List
    [Documentation]    Navigate to Agents list (handles detail-open SPA state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-agents']
    Sleep    1s
    # SPA may open to agent detail if previously selected
    ${list_count}=    Get Element Count    text=/\\d+ agents registered/
    IF    ${list_count} == 0
        # In detail view - click back button (data-testid preferred)
        ${back_testid}=    Get Element Count    [data-testid='agent-detail-back-btn']
        IF    ${back_testid} > 0
            Click    [data-testid='agent-detail-back-btn']
        ELSE
            ${back_count}=    Get Element Count    button:has-text("󰁍")
            IF    ${back_count} > 0
                Click    button:has-text("󰁍") >> nth=0
            END
        END
    END
    Wait For Elements State    text=/\\d+ agents registered/    visible    timeout=20s

Navigate To Search View
    [Documentation]    Navigate to Search view
    Navigate To Dashboard Home
    Click    [data-testid='nav-search']
    Wait For Elements State    text=Evidence Search    visible    timeout=${ELEMENT_TIMEOUT}

Navigate To Executive View
    [Documentation]    Navigate to Executive view
    Navigate To Dashboard Home
    Click    [data-testid='nav-executive']
    Wait For Elements State    text=Executive Report    visible    timeout=${ELEMENT_TIMEOUT}

Navigate To Rules List
    [Documentation]    Navigate to Rules list (handles detail-open state)
    Navigate To Dashboard Home
    Click    [data-testid='nav-rules']
    ${list_count}=    Get Element Count    text=/\\d+ rules loaded/
    IF    ${list_count} == 0
        ${back_count}=    Get Element Count    button:has-text("󰁍")
        IF    ${back_count} > 0
            Click    button:has-text("󰁍") >> nth=0
        END
    END
    Wait For Elements State    text=/\\d+ rules loaded/    visible    timeout=20s

*** Test Cases ***
# =============================================================================
# Decisions View Tests
# =============================================================================

Decisions View Loads
    [Documentation]    Decision Log view loads with header
    [Tags]    e2e    browser    decisions    smoke
    [Setup]    Navigate To Decisions List
    Wait For Elements State    [data-testid='decision-log']    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Decisions Shows Count
    [Documentation]    Decision Log shows number of decisions
    [Tags]    e2e    browser    decisions
    [Setup]    Navigate To Decisions List
    Wait For Elements State    text=/\\d+ decisions in log/    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Decisions Add Button Present
    [Documentation]    Record Decision button is visible
    [Tags]    e2e    browser    decisions
    [Setup]    Navigate To Decisions List
    Wait For Elements State    [data-testid='decisions-add-btn']    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Decisions Session Filter Present
    [Documentation]    Session filter dropdown is visible
    [Tags]    e2e    browser    decisions    filter
    [Setup]    Navigate To Decisions List
    Wait For Elements State    [data-testid='decision-session-filter']    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Decision List Has Items
    [Documentation]    Decision log shows at least one decision item
    [Tags]    e2e    browser    decisions
    [Setup]    Navigate To Decisions List
    ${count}=    Get Element Count    [data-testid='decision-log-item']
    Should Be True    ${count} > 0
    ...    msg=Expected at least 1 decision item, got ${count}

Click Decision Shows Detail
    [Documentation]    Clicking a decision opens detail view
    [Tags]    e2e    browser    decisions    detail
    [Setup]    Navigate To Decisions List
    ${count}=    Get Element Count    [data-testid='decision-log-item']
    Skip If    ${count} == 0    No decisions to click
    Click    [data-testid='decision-log-item'] >> nth=0
    Wait For Elements State    text=Decision Information    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Decision Detail Shows Status
    [Documentation]    Decision detail shows status chip
    [Tags]    e2e    browser    decisions    detail
    [Setup]    Navigate To Decisions List
    ${count}=    Get Element Count    [data-testid='decision-log-item']
    Skip If    ${count} == 0    No decisions to click
    Click    [data-testid='decision-log-item'] >> nth=0
    Wait For Elements State    [data-testid='decision-detail-status']    visible
    ...    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Agents View Tests (List + Detail)
# =============================================================================

Agents View Loads
    [Documentation]    Agents view loads with registered agents header
    [Tags]    e2e    browser    agents    smoke
    [Setup]    Navigate To Agents List
    Wait For Elements State    text=/\\d+ agents registered/    visible

Agents Shows Count
    [Documentation]    Agents view shows agent count
    [Tags]    e2e    browser    agents
    [Setup]    Navigate To Agents List
    Wait For Elements State    text=/\\d+ agents registered/    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Agent List Has Items
    [Documentation]    At least one agent is listed
    [Tags]    e2e    browser    agents
    [Setup]    Navigate To Agents List
    ${count}=    Get Element Count    text=/curator-agent|orchestrator|claude-code|Claude Code/
    Should Be True    ${count} > 0
    ...    msg=Expected at least 1 known agent in list, got ${count}

Click Agent Shows Detail
    [Documentation]    Clicking an agent shows detail view with metrics
    [Tags]    e2e    browser    agents    detail
    [Setup]    Navigate To Agents List
    ${count}=    Get Element Count    text=/curator-agent|orchestrator|claude-code|Claude Code/
    Skip If    ${count} == 0    No agents to click
    Click    text=/curator-agent|orchestrator|claude-code|Claude Code/ >> nth=0
    Wait For Elements State    [data-testid='agent-metrics-card']    visible
    ...    timeout=${ELEMENT_TIMEOUT}

Agent Detail Shows Trust Score
    [Documentation]    Agent detail shows trust score metric
    [Tags]    e2e    browser    agents    detail
    [Setup]    Navigate To Agents List
    ${count}=    Get Element Count    text=/curator-agent|orchestrator|claude-code|Claude Code/
    Skip If    ${count} == 0    No agents to click
    Click    text=/curator-agent|orchestrator|claude-code|Claude Code/ >> nth=0
    Wait For Elements State    [data-testid='agent-metrics-card'] >> text=Trust Score    visible    timeout=${ELEMENT_TIMEOUT}

Agent Detail Shows Trust History
    [Documentation]    Agent detail shows trust history card
    [Tags]    e2e    browser    agents    detail
    [Setup]    Navigate To Agents List
    ${count}=    Get Element Count    text=/curator-agent|orchestrator|claude-code|Claude Code/
    Skip If    ${count} == 0    No agents to click
    Click    text=/curator-agent|orchestrator|claude-code|Claude Code/ >> nth=0
    Wait For Elements State    [data-testid='agent-trust-history-card']    visible
    ...    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Search View Tests
# =============================================================================

Search View Loads
    [Documentation]    Search view loads with Evidence Search header
    [Tags]    e2e    browser    search    smoke
    [Setup]    Navigate To Search View
    Wait For Elements State    text=Evidence Search    visible

Search Has Input Field
    [Documentation]    Search view has a text input for queries
    [Tags]    e2e    browser    search
    [Setup]    Navigate To Search View
    ${count}=    Get Element Count    input
    Should Be True    ${count} > 0
    ...    msg=Expected search input field, got ${count} inputs

# =============================================================================
# Executive View Tests
# =============================================================================

Executive View Loads
    [Documentation]    Executive view loads with report header
    [Tags]    e2e    browser    executive    smoke
    [Setup]    Navigate To Executive View
    Wait For Elements State    text=Executive Report    visible

Executive Shows Summary
    [Documentation]    Executive view shows Executive Summary section
    [Tags]    e2e    browser    executive
    [Setup]    Navigate To Executive View
    Wait For Elements State    text=Executive Summary    visible    timeout=${ELEMENT_TIMEOUT}

Executive Shows Compliance
    [Documentation]    Executive view shows Compliance Status section
    [Tags]    e2e    browser    executive
    [Setup]    Navigate To Executive View
    Wait For Elements State    text=Compliance Status    visible    timeout=${ELEMENT_TIMEOUT}

Executive Shows Stat Cards
    [Documentation]    Executive view shows stat cards (Rules, Agents, Tasks)
    [Tags]    e2e    browser    executive
    [Setup]    Navigate To Executive View
    Wait For Elements State    text=Rules >> nth=0    visible    timeout=${ELEMENT_TIMEOUT}
    Wait For Elements State    text=Agents >> nth=0    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Rules Search Tests (functional)
# =============================================================================

Rules Search Input Accepts Text
    [Documentation]    Rules search input can receive text
    [Tags]    e2e    browser    rules    search    functional
    [Setup]    Navigate To Rules List
    ${count}=    Get Element Count    input[type='text']
    Skip If    ${count} == 0    No text input found on rules page
    Fill Text    input[type='text'] >> nth=0    ARCH
    Sleep    1s
    Wait For Elements State    text=/\\d+ rules loaded/    visible    timeout=${ELEMENT_TIMEOUT}

# =============================================================================
# Cross-View Navigation Tests
# =============================================================================

Navigate All Major Views In Sequence
    [Documentation]    Navigate through all major views without errors
    [Tags]    e2e    browser    navigation    smoke    regression
    # Rules
    Click    [data-testid='nav-rules']
    Sleep    2s
    # Decisions
    Click    [data-testid='nav-decisions']
    Sleep    2s
    # Agents
    Click    [data-testid='nav-agents']
    Sleep    2s
    # Tasks
    Click    [data-testid='nav-tasks']
    Sleep    2s
    # Sessions
    Click    [data-testid='nav-sessions']
    Sleep    2s
    # Trust
    Click    [data-testid='nav-trust']
    Sleep    2s
    # Executive
    Click    [data-testid='nav-executive']
    Sleep    2s
    # Infrastructure
    Click    [data-testid='nav-infra']
    Wait For Elements State    text=Infrastructure Health    visible    timeout=${ELEMENT_TIMEOUT}
    # Search
    Click    [data-testid='nav-search']
    Wait For Elements State    text=Evidence Search    visible    timeout=${ELEMENT_TIMEOUT}
    # Header still visible
    Wait For Elements State    text=${APP_TITLE}    visible
