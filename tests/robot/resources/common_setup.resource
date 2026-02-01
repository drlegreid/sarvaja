*** Settings ***
Documentation    Shared Suite Setup/Teardown and common keywords.
...              Per D.3: Robot Framework test refactoring (SRP/OOP/DRY).
...              Per PLAN-UI-OVERHAUL-001 Task D.3.
...
...              Usage:
...              Resource    ../resources/common_setup.resource
...              Suite Setup    Platform Setup
...              Suite Teardown    Platform Teardown
Resource         common.resource

*** Keywords ***
Platform Setup
    [Documentation]    Standard suite-level setup: verify API health, log environment.
    Log    Platform Setup: API_BASE=${API_BASE}, DASHBOARD_URL=${DASHBOARD_URL}
    ${api_ok}=    Check API Available
    Set Suite Variable    ${API_AVAILABLE}    ${api_ok}
    Run Keyword If    not ${api_ok}    Log    WARNING: API not available - some tests will skip    WARN

Platform Teardown
    [Documentation]    Standard suite-level teardown: log summary.
    Log    Platform Teardown complete

Check API Available
    [Documentation]    Check if the governance API is reachable. Returns boolean.
    ${status}=    Evaluate    __import__('urllib.request').request.urlopen('${API_BASE}/api/health', timeout=3).status == 200
    ...    modules=urllib.request
    [Return]    ${status}
    [Teardown]    Run Keyword If Test Failed    Set Variable    ${FALSE}

Handle Skippable Result
    [Documentation]    Common pattern: check if result has skipped=True and skip test.
    ...                Replaces the repeated 3-line skip pattern across tests.
    ...                Usage: Handle Skippable Result    ${result}
    [Arguments]    ${result}    ${default_reason}=Check not available
    ${skipped}=    Evaluate    $result.get('skipped', False)
    ${reason}=     Evaluate    $result.get('reason', '${default_reason}')
    Skip If    ${skipped}    ${reason}

Assert Result Healthy
    [Documentation]    Common pattern: verify result dict has healthy=True.
    ...                Usage: Assert Result Healthy    ${result}    TypeDB
    [Arguments]    ${result}    ${service_name}=Service
    Handle Skippable Result    ${result}    ${service_name} check skipped
    Should Be True    ${result}[healthy]    ${service_name} unhealthy: ${result}

Require TypeDB
    [Documentation]    Skip test if TypeDB is not connected.
    ...                Usage as Test Setup: Require TypeDB
    ${result}=    Evaluate    __import__('urllib.request').request.urlopen('${API_BASE}/api/health', timeout=3).read()
    ...    modules=urllib.request
    ${health}=    Evaluate    __import__('json').loads($result)    modules=json
    ${typedb}=    Evaluate    $health.get('typedb_connected', False)
    Skip If    not ${typedb}    TypeDB not connected

Require API
    [Documentation]    Skip test if API is not available.
    Skip If    not ${API_AVAILABLE}    API not available
