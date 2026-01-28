*** Settings ***
Documentation    BDD Tests for Rules API
...              Per RF-006: E2E tests using BDD syntax
...              Per GAP-UI-AUDIT-001: Validates rule-document linkage
Resource         ../resources/api_client.robot
Library          Collections
Suite Setup      Create API Session
Test Tags        e2e    rules    critical    GAP-UI-AUDIT-001    GOV-RULE-01-v1    create    read    update    delete

*** Test Cases ***
Rule Should Have Document Path When Linked
    [Documentation]    Per GAP-UI-AUDIT-001: Rules should show document_path
    [Tags]    TASK-VALID-01-v1    regression
    Given The API Server Is Running
    When I Request Rule Details For "TASK-VALID-01-v1"
    Then The Response Status Should Be 200
    And The Rule Should Have A Document Path

Rules List Should Include Document Paths
    [Documentation]    Per GAP-UI-AUDIT-001: List should include document_path
    [Tags]    regression
    Given The API Server Is Running
    When I Request The Rules List
    Then The Response Status Should Be 200
    And At Least One Rule Should Have Document Path

*** Keywords ***
The API Server Is Running
    [Documentation]    Verify API health check passes
    ${response}=    GET API Endpoint    /health
    Verify Status Code    ${response}    200
    Log    Intent: Verify API server is healthy

I Request Rule Details For "${rule_id}"
    [Documentation]    Fetch specific rule by ID
    ${response}=    GET API Endpoint    /rules/${rule_id}
    Set Test Variable    ${RESPONSE}    ${response}
    Log    Action: GET /api/rules/${rule_id}

I Request The Rules List
    [Documentation]    Fetch all rules with pagination
    ${response}=    GET API Endpoint    /rules?limit=50
    Set Test Variable    ${RESPONSE}    ${response}
    Log    Action: GET /api/rules

The Response Status Should Be ${expected_code}
    [Documentation]    Assert HTTP status code
    Verify Status Code    ${RESPONSE}    ${expected_code}
    Log    Effect: Status code is ${expected_code}

The Rule Should Have A Document Path
    [Documentation]    Assert document_path field is present and not null
    ${json}=    Set Variable    ${RESPONSE.json()}
    Dictionary Should Contain Key    ${json}    document_path
    Should Not Be Equal    ${json}[document_path]    ${None}
    Log    Evidence: document_path = ${json}[document_path]

At Least One Rule Should Have Document Path
    [Documentation]    Assert at least one rule has document_path
    ${rules}=    Set Variable    ${RESPONSE.json()}
    ${found}=    Set Variable    ${False}
    FOR    ${rule}    IN    @{rules}
        ${has_path}=    Run Keyword And Return Status
        ...    Should Not Be Equal    ${rule}[document_path]    ${None}
        IF    ${has_path}
            ${found}=    Set Variable    ${True}
            Log    Evidence: ${rule}[id] has document_path = ${rule}[document_path]
            BREAK
        END
    END
    Should Be True    ${found}    msg=No rules have document_path set
