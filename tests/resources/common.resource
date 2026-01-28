*** Settings ***
Documentation    Common resources for all E2E tests
...              Per RF-001: Base keyword library
...              Per TEST-BDD-01-v1: BDD E2E Testing Standard

Library    Browser    auto_closing_level=SUITE
Library    Collections
Library    String
Library    DateTime
Library    RequestsLibrary

*** Variables ***
${BASE_URL}        http://localhost:8081
${API_URL}         http://localhost:8082/api
${TIMEOUT}         30s
${BROWSER}         chromium
${HEADLESS}        True
${CONTENT_TYPE}    application/json

*** Keywords ***
# === Session Management ===
Create API Session
    [Documentation]    Create HTTP session for API testing
    [Tags]    api
    Create Session    api    ${API_URL}    verify=${False}

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

# === API Keywords ===
API GET
    [Documentation]    Send GET request to API endpoint
    [Arguments]    ${endpoint}    ${params}=${None}
    [Tags]    api
    ${response}=    GET On Session    api    ${endpoint}    params=${params}    expected_status=any
    RETURN    ${response}

API POST
    [Documentation]    Send POST request to API endpoint
    [Arguments]    ${endpoint}    ${data}=${None}
    [Tags]    api
    ${headers}=    Create Dictionary    Content-Type=${CONTENT_TYPE}
    ${response}=    POST On Session    api    ${endpoint}    json=${data}    headers=${headers}    expected_status=any
    RETURN    ${response}

API PUT
    [Documentation]    Send PUT request to API endpoint
    [Arguments]    ${endpoint}    ${data}=${None}
    [Tags]    api
    ${headers}=    Create Dictionary    Content-Type=${CONTENT_TYPE}
    ${response}=    PUT On Session    api    ${endpoint}    json=${data}    headers=${headers}    expected_status=any
    RETURN    ${response}

API DELETE
    [Documentation]    Send DELETE request to API endpoint
    [Arguments]    ${endpoint}
    [Tags]    api
    ${response}=    DELETE On Session    api    ${endpoint}    expected_status=any
    RETURN    ${response}

# === Assertions ===
Response Status Should Be
    [Documentation]    Verify response status code
    [Arguments]    ${response}    ${expected_status}
    [Tags]    api    assertion
    Should Be Equal As Integers    ${response.status_code}    ${expected_status}

Response Should Contain
    [Documentation]    Verify response body contains key
    [Arguments]    ${response}    ${key}
    [Tags]    api    assertion
    ${json}=    Set Variable    ${response.json()}
    Dictionary Should Contain Key    ${json}    ${key}

Dashboard Should Be Visible
    [Documentation]    Verify dashboard has loaded
    [Tags]    ui
    Wait For Elements State    css=.v-app    visible    timeout=${TIMEOUT}

# === Navigation ===
Navigate To Tab
    [Documentation]    Navigate to a specific dashboard tab
    [Arguments]    ${tab_name}
    [Tags]    ui
    Click    css=[data-testid='nav-${tab_name.lower()}']
    Wait For Load State    networkidle

# === Evidence ===
Take Evidence Screenshot
    [Documentation]    Capture screenshot for test evidence
    [Arguments]    ${name}=screenshot
    [Tags]    evidence
    ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
    Take Screenshot    evidence_${name}_${timestamp}.png

Health Check Should Pass
    [Documentation]    Verify API health endpoint returns 200
    [Tags]    api    smoke
    Create API Session
    ${response}=    API GET    /health
    Response Status Should Be    ${response}    200
