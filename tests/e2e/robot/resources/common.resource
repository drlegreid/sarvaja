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

# Test Data Isolation (TEST-DATA-01-v1)
# All test entities MUST use sandbox workspace, NEVER production WS-9147535A
${TEST_WORKSPACE}          WS-TEST-SANDBOX
${TEST_PROJECT}            sarvaja-test

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

# --- Test Data Lifecycle (TEST-DATA-01-v1) ---

Create Test Task
    [Documentation]    Create a task in sandbox workspace via REST API.
    ...                Per TEST-DATA-01-v1: Always uses ${TEST_WORKSPACE}.
    ...                Returns task_id for cleanup in [Teardown].
    [Arguments]    ${summary}=RF > Test > Default    ${task_type}=test    ${priority}=LOW
    ${timestamp}=    Get Current Date    result_format=%Y%m%d%H%M%S
    ${task_id}=    Set Variable    RF-QUAL-${timestamp}
    ${body}=    Create Dictionary
    ...    task_id=${task_id}
    ...    summary=${summary}
    ...    description=${summary}
    ...    task_type=${task_type}
    ...    priority=${priority}
    ...    workspace_id=${TEST_WORKSPACE}
    ...    phase=P10
    ${resp}=    Http    ${API_URL}/tasks    POST    ${body}
    Should Be Equal As Integers    ${resp}[status]    201
    RETURN    ${task_id}

Delete Test Task
    [Documentation]    Delete a test task by ID. Safe to call on already-deleted tasks.
    ...                Per TEST-DATA-01-v1: Use in [Teardown] for atomic cleanup.
    [Arguments]    ${task_id}
    ${resp}=    Http    ${API_URL}/tasks/${task_id}    DELETE
    Log    Deleted test task ${task_id}: ${resp}[status]
