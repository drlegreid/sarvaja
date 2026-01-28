*** Settings ***
Documentation    Common resources for all E2E tests
...              Per RF-001: Base keyword library
...              Per TEST-BDD-01-v1: BDD E2E Testing Standard

Library    Browser    auto_closing_level=SUITE
Library    Collections
Library    String
Library    DateTime

*** Variables ***
${BASE_URL}        http://localhost:8081
${API_URL}         http://localhost:8082/api
${TIMEOUT}         30s
${BROWSER}         chromium
${HEADLESS}        True

*** Keywords ***
Open Dashboard
    [Documentation]    Open the governance dashboard in browser
    [Tags]    ui
    New Browser    ${BROWSER}    headless=${HEADLESS}
    New Page    ${BASE_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}

Close Dashboard
    [Documentation]    Close browser session
    [Tags]    ui
    Close Browser

Dashboard Should Be Visible
    [Documentation]    Verify dashboard has loaded
    [Tags]    ui
    Wait For Elements State    css=.v-app    visible    timeout=${TIMEOUT}

Navigate To Tab
    [Documentation]    Navigate to a specific dashboard tab
    [Arguments]    ${tab_name}
    [Tags]    ui
    Click    css=[data-testid='nav-${tab_name.lower()}']
    Wait For Load State    networkidle

Take Evidence Screenshot
    [Documentation]    Capture screenshot for test evidence
    [Arguments]    ${name}=screenshot
    [Tags]    evidence
    ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    Take Screenshot    evidence_${name}_${timestamp}.png

Log API Response
    [Documentation]    Log API response for debugging
    [Arguments]    ${response}
    [Tags]    api    debug
    Log    Status: ${response.status}
    Log    Body: ${response.body}
