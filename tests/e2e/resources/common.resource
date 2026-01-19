*** Settings ***
Documentation    Common resources for Sarvaja E2E tests
...              Provides API helpers, configuration, and shared keywords
...              Per RULE-023: Test Before Ship
Library          Browser    auto_closing_level=KEEP
Library          Collections
Library          RequestsLibrary

*** Variables ***
${BASE_URL}           http://localhost:8081
${API_BASE_URL}       http://localhost:8082
${TIMEOUT}            30s

*** Keywords ***
# =============================================================================
# SETUP & TEARDOWN
# =============================================================================

Setup Test Suite
    [Documentation]    Initialize browser and API session
    New Browser    chromium    headless=true
    New Context    viewport={'width': 1280, 'height': 720}
    Create Session    api    ${API_BASE_URL}    verify=${FALSE}

Teardown Test Suite
    [Documentation]    Close all browsers safely
    ${status}=    Run Keyword And Return Status    Close Browser    ALL
    Log    Browser close status: ${status}

# =============================================================================
# API HELPERS
# =============================================================================

Get Tasks Via API
    [Documentation]    Fetch all tasks from API
    ${response}=    GET On Session    api    /api/tasks    params=limit=200
    Should Be Equal As Integers    ${response.status_code}    200
    RETURN    ${response.json()}

Get Sessions Via API
    [Documentation]    Fetch all sessions from API
    ${response}=    GET On Session    api    /api/sessions    params=limit=200
    Should Be Equal As Integers    ${response.status_code}    200
    RETURN    ${response.json()}

Get Agents Via API
    [Documentation]    Fetch all agents from API
    ${response}=    GET On Session    api    /api/agents
    Should Be Equal As Integers    ${response.status_code}    200
    RETURN    ${response.json()}

Get Rules Via API
    [Documentation]    Fetch all rules from API
    ${response}=    GET On Session    api    /api/rules    params=limit=200
    Should Be Equal As Integers    ${response.status_code}    200
    RETURN    ${response.json()}

Get Field Values
    [Documentation]    Extract all values for a field from a list of dicts
    [Arguments]    ${items}    ${field}
    ${values}=    Create List
    FOR    ${item}    IN    @{items}
        ${value}=    Get From Dictionary    ${item}    ${field}    default=${NONE}
        Run Keyword If    '${value}' != 'None'
        ...    Append To List    ${values}    ${value}
    END
    RETURN    ${values}

# =============================================================================
# UI NAVIGATION
# =============================================================================

Navigate To Dashboard
    [Documentation]    Navigate to main dashboard
    New Page    ${BASE_URL}
    Wait For Load State    networkidle    timeout=${TIMEOUT}

Navigate To Rules View
    [Documentation]    Navigate to rules management view
    Navigate To Dashboard
    Click    [data-testid="nav-rules"]
    Wait For Load State    networkidle

Navigate To Tasks View
    [Documentation]    Navigate to tasks management view
    Navigate To Dashboard
    Click    [data-testid="nav-tasks"]
    Wait For Load State    networkidle

Navigate To Sessions View
    [Documentation]    Navigate to sessions view
    Navigate To Dashboard
    Click    [data-testid="nav-sessions"]
    Wait For Load State    networkidle

Navigate To Agents View
    [Documentation]    Navigate to agents view
    Navigate To Dashboard
    Click    [data-testid="nav-agents"]
    Wait For Load State    networkidle
