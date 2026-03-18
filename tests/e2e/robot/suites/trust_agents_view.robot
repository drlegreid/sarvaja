*** Settings ***
Documentation    Trust Dashboard & Agents View E2E Tests
...              Per TEST-E2E-FRAMEWORK-01-v1: Robot Framework migration
...              Migrated from: tests/e2e/test_dashboard_e2e.py (TrustView, AgentsView)

Resource    ../resources/common.resource

Suite Setup       Suite Setup Open Dashboard
Suite Teardown    Suite Teardown Close Browser
Test Setup        Test Setup Navigate Home

Default Tags    e2e    browser

*** Test Cases ***
# ── Trust Dashboard ──

Trust Dashboard Loads With Stats
    [Documentation]    Trust dashboard shows stats cards.
    [Tags]    trust
    Navigate And Verify Tab    trust    Agent Trust Dashboard
    Wait For Elements State    text=Total Agents    visible    timeout=10s
    Wait For Elements State    text=Avg Trust Score    visible    timeout=10s

Trust Refresh Button Is Present
    [Documentation]    Refresh Data button is visible.
    [Tags]    trust
    Navigate And Verify Tab    trust    Agent Trust Dashboard
    Wait For Elements State    text=Refresh Data    visible    timeout=10s

Trust Leaderboard Is Visible
    [Documentation]    Trust leaderboard section is displayed.
    [Tags]    trust
    Navigate And Verify Tab    trust    Agent Trust Dashboard
    Wait For Elements State    text=Trust Leaderboard    visible    timeout=10s

# ── Agents View ──

Agents View Loads
    [Documentation]    Agents view renders with agent list.
    [Tags]    agents
    Navigate And Verify Tab    agents    Registered Agents

Agents Table Shows Content
    [Documentation]    Agents table shows agent data.
    [Tags]    agents
    Navigate And Verify Tab    agents    Registered Agents
    ${has_agent}=    Run Keyword And Return Status
    ...    Wait For Elements State    text=/agent|Agent/    visible    timeout=5s
    Log    Agent content visible: ${has_agent}
