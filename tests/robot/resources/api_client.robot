*** Settings ***
Documentation    API Client Keywords for Governance API
...              Per RF-002: Base keyword library for API testing
Library          RequestsLibrary
Library          Collections

*** Variables ***
${BASE_URL}    http://localhost:8082/api

*** Keywords ***
Create API Session
    [Documentation]    Initialize HTTP session for API calls
    Create Session    api    ${BASE_URL}    verify=${False}

GET API Endpoint
    [Arguments]    ${endpoint}
    [Documentation]    Make GET request to API endpoint
    ${response}=    GET On Session    api    ${endpoint}
    RETURN    ${response}

POST API Endpoint
    [Arguments]    ${endpoint}    ${body}
    [Documentation]    Make POST request to API endpoint
    ${response}=    POST On Session    api    ${endpoint}    json=${body}
    RETURN    ${response}

Verify Status Code
    [Arguments]    ${response}    ${expected_code}
    [Documentation]    Assert response has expected status code
    Should Be Equal As Integers    ${response.status_code}    ${expected_code}

Verify Response Contains
    [Arguments]    ${response}    ${key}
    [Documentation]    Assert response JSON contains expected key
    Dictionary Should Contain Key    ${response.json()}    ${key}
