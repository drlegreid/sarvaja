*** Settings ***
Documentation    Common resources for all E2E test suites
...              Per TEST-E2E-FRAMEWORK-01-v1: Centralized setup, DRY keywords
...              Per TEST-BDD-01-v1: BDD E2E Testing Standard

Library    Browser    auto_closing_level=SUITE
Library    Collections
Library    String
Library    DateTime
Library    ../libraries/actions.py
Library    ../libraries/navigation.py
Library    ../libraries/overlay.py

Resource    selectors.resource

*** Variables ***
${API_URL}         http://localhost:8082/api
${TIMEOUT}         30s
${BROWSER}         chromium
${HEADLESS}        true

# Agent IDs — sourced from governance/stores/agents.py:_AGENT_BASE_CONFIG
# DRY: All Robot suites MUST use these variables, not hardcoded strings
${DEFAULT_AGENT}           code-agent
@{VALID_AGENTS}            code-agent    task-orchestrator    rules-curator    research-agent    local-assistant

*** Keywords ***
Suite Setup Open Dashboard
    [Documentation]    Opens browser, navigates to dashboard, injects overlay fix.
    ...                Used as Suite Setup for all browser E2E test suites.
    New Browser    ${BROWSER}    headless=${HEADLESS}
    &{vp}=    Create Dictionary    width=${1280}    height=${720}
    New Context    viewport=${vp}    ignoreHTTPSErrors=${TRUE}
    Open Dashboard    ${DASHBOARD_URL}
    Dashboard Should Be Loaded    ${APP_TITLE}
    Inject Overlay Fix

Suite Teardown Close Browser
    [Documentation]    Closes all browser resources cleanly.
    Close Browser    ALL

Test Setup Navigate Home
    [Documentation]    Reloads dashboard to reset Trame state between tests.
    ...                Ensures each test starts from a clean dashboard.
    Go To    ${DASHBOARD_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}
    Dashboard Should Be Loaded    ${APP_TITLE}
    Inject Overlay Fix

Navigate And Verify Tab
    [Documentation]    Navigate to a tab and verify expected content loaded.
    ...                Uses Fibonacci backoff for the content check.
    [Arguments]    ${tab_name}    ${expected_text}
    Navigate To Tab    ${tab_name}
    Element Should Be Visible With Backoff    text=${expected_text}

Verify Data Table Has Rows
    [Documentation]    Wait for a data table to have at least one data row.
    ...                Uses Fibonacci backoff via actions library.
    [Arguments]    ${table_selector}=tbody    ${max_attempts}=6
    Wait For Table Rows    ${table_selector}    ${max_attempts}

Take Evidence Screenshot
    [Documentation]    Capture screenshot for test evidence.
    [Arguments]    ${name}=screenshot
    ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    Take Screenshot    evidence_${name}_${timestamp}.png
