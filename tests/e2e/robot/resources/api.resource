*** Settings ***
Documentation    API Testing Keywords
...              Per RF-001: REST API test keywords
...              Per TEST-COMP-01-v1: Deterministic assertions

Library    RequestsLibrary
Library    Collections
Library    JSONLibrary

*** Variables ***
${API_URL}         http://localhost:8082/api
${CONTENT_TYPE}    application/json

*** Keywords ***
Create API Session
    [Documentation]    Create HTTP session for API testing
    [Tags]    api
    Create Session    api    ${API_URL}    verify=${False}

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

Health Check Should Pass
    [Documentation]    Verify API health endpoint returns 200
    [Tags]    api    smoke
    Create API Session
    ${response}=    API GET    /health
    Response Status Should Be    ${response}    200
